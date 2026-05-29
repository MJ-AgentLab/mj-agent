"""scripts/sdd/_common/bdd_helpers.py — Stage D D-2 deploy (8th _common/ module).

Shared infra for BDD validators per Stage D outline §3 v2 + R-N v2 R-4:

- G19 (D-2 BLOCKING; ``check_bdd_scenario_trace.py``) — FULL usage
- G21 (D-3 WARNING; ``check_bdd_acceptance.py``) — subset (parse + extract)
- G22 (D-4 WARNING; ``check_bdd_unautomated.py``) — subset (parse + extract + load_trace_yml)

G20 / G27 / G28 NOT in Phase M4 scope (per gates.md L96 Option A); future
helpers (e.g. ``count_steps``) added via additive expansion per §5 stability
commitment.

Minimal custom gherkin parser (Feature/Scenario names + tags only; no step
body parsing — sufficient for G19/G21/G22). Avoids heavy gherkin library.

Tag canonical pattern (per behavior.feature 17-scenario empirical inventory):

- ``@REQ-NNN``           — capability REQ id
- ``@CTR-<slug>``        — contract slug
- ``@risk:<level>``      — risk level (critical/major/minor/high/medium/low)
- ``@adapter:<name>``    — adapter ref
- Other (uncategorized): ``@meta-gate:Axx`` / ``@reference-contract`` /
  ``@adr:ADR-NNN`` / etc. — fall into ``other`` bucket

Grammar change → triggers M-FU register + R-N reframe approval per §5.

Policy separation (R-N v8 R-1 supersedes R-N v7 R-1; Stage D D-2 Step 5
escalation lock-in): helpers return FACTS (binding flags + descriptive
messages); FAIL/WARN/PASS POLICY decided by validator per Decision Matrix
(TAG layer = FAIL on @REQ/@CTR missing; TRACE layer = WARN on trace.yml
bdd 层 mapping gap; healthy = PASS).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# Tag pattern constants — pinned grammar (Stage D D-2 R-N v7 N-1).
# Grammar change → M-FU register + R-N reframe per §5 stability commitment.
_REQ_PATTERN = re.compile(r"^@(REQ-\d+)$")
_CTR_PATTERN = re.compile(r"^@CTR-([a-z0-9-]+)$")
_RISK_PATTERN = re.compile(r"^@risk:(critical|major|minor|high|medium|low)$")
_ADAPTER_PATTERN = re.compile(r"^@adapter:([a-z0-9-]+)$")


class FeatureParseError(ValueError):
    """Raised when .feature parsing fails (caller catches → validator WARN)."""


@dataclass(frozen=True)
class Scenario:
    """Single Scenario (or Scenario Outline) within a Feature."""

    name: str
    tags: list[str]
    line: int
    is_outline: bool = False


@dataclass(frozen=True)
class Feature:
    """Parsed .feature file representation."""

    name: str
    feature_tags: list[str]
    scenarios: list[Scenario]
    path: Path


@dataclass(frozen=True)
class ScenarioTags:
    """Tags bucketed by canonical pattern (per N-1 grammar pin)."""

    req: list[str]
    ctr: list[str]
    risk: list[str]
    adapter: list[str]
    other: list[str]


@dataclass
class TraceResult:
    """Per-scenario REQ/CTR trace verdict (G19; non-frozen for messages.append)."""

    scenario_name: str
    has_req_tag: bool
    has_ctr_tag: bool
    req_bound_in_trace: bool
    ctr_bound_in_trace: bool
    messages: list[str] = field(default_factory=list)


def parse_feature_file(path: Path) -> Feature:
    """Parse .feature file → ``Feature`` dataclass.

    Minimal custom gherkin parser: extracts Feature/Scenario names + tags only
    (no step body parsing; sufficient for G19/G21/G22).

    Raises:
        FeatureParseError: gherkin syntax invalid (no ``Feature:`` keyword found)
            OR file unreadable. Caller catches and converts to validator WARN
            per Stage A ``precheck.sqlglot_parse_failed`` graceful-fallback precedent.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FeatureParseError(f"{path}: cannot read file ({exc})") from exc

    feature_name: str | None = None
    feature_tags: list[str] = []
    scenarios: list[Scenario] = []
    pending_tags: list[str] = []

    for line_num, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("@"):
            for token in line.split():
                if token.startswith("@"):
                    pending_tags.append(token)
            continue

        if line.startswith("Feature:"):
            feature_name = line[len("Feature:"):].strip()
            feature_tags = pending_tags.copy()
            pending_tags = []
            continue

        is_outline = line.startswith("Scenario Outline:")
        is_scenario = line.startswith("Scenario:") and not is_outline
        if is_scenario or is_outline:
            keyword_len = len("Scenario Outline:") if is_outline else len("Scenario:")
            scenario_name = line[keyword_len:].strip()
            scenarios.append(Scenario(
                name=scenario_name,
                tags=pending_tags.copy(),
                line=line_num,
                is_outline=is_outline,
            ))
            pending_tags = []
            continue

        # Other lines (Background, Given/When/Then/And/But, Examples, table rows, etc.)
        # are ignored. Pending tags survive only across blank/comment lines; any
        # other content line clears them (defensive: well-formed gherkin won't hit this).

    if feature_name is None:
        raise FeatureParseError(f"{path}: no 'Feature:' keyword found")

    return Feature(
        name=feature_name,
        feature_tags=feature_tags,
        scenarios=scenarios,
        path=path,
    )


def extract_tags(scenario: Scenario) -> ScenarioTags:
    """Bucket scenario tags into typed categories per canonical pattern.

    Pure post-parse function; never raises. Unknown tags fall into ``other``.
    """
    req: list[str] = []
    ctr: list[str] = []
    risk: list[str] = []
    adapter: list[str] = []
    other: list[str] = []

    for tag in scenario.tags:
        if (m := _REQ_PATTERN.match(tag)):
            req.append(m.group(1))
        elif (m := _CTR_PATTERN.match(tag)):
            ctr.append(m.group(1))
        elif (m := _RISK_PATTERN.match(tag)):
            risk.append(m.group(1))
        elif (m := _ADAPTER_PATTERN.match(tag)):
            adapter.append(m.group(1))
        else:
            other.append(tag)

    return ScenarioTags(req=req, ctr=ctr, risk=risk, adapter=adapter, other=other)


def load_trace_yml(capability_dir: Path) -> dict | None:
    """Load ``<capability_dir>/trace.yml``; return ``None`` on missing/error.

    Graceful ``None`` pattern per Stage A ``_common.frontmatter.parse_frontmatter``
    precedent. Caller distinguishes missing (None) vs valid-with-no-bdd-layer
    (dict with no ``bdd`` key) per R-N v7 R-1 graceful handling.
    """
    trace_path = capability_dir / "trace.yml"
    if not trace_path.exists():
        return None
    try:
        with trace_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except (yaml.YAMLError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def trace_req_ctr(scenario: Scenario, trace_data: dict) -> TraceResult:
    """G19: extract scenario REQ/CTR binding FACTS (helper layer; NO policy).

    Per R-N v8 R-1 (supersedes R-N v7 R-1): helper returns FACTS (binding
    flags + descriptive messages); FAIL/WARN/PASS POLICY decided by validator
    per Decision Matrix (TAG layer = FAIL on @REQ/@CTR missing; TRACE layer
    = WARN on trace.yml bdd 层 mapping gap; healthy = PASS).

    Args:
        scenario: parsed ``Scenario`` with tags
        trace_data: trace.yml mapping (from ``load_trace_yml``; non-None)

    Returns:
        ``TraceResult`` — per-scenario binding facts (4 bool flags + descriptive
        messages list). Validator consumes flags directly for policy routing.
    """
    tags = extract_tags(scenario)
    has_req_tag = len(tags.req) > 0
    has_ctr_tag = len(tags.ctr) > 0

    req_bound_in_trace = False
    ctr_bound_in_trace = False

    links = trace_data.get("links") if isinstance(trace_data, dict) else None
    if isinstance(links, list):
        for link in links:
            if not isinstance(link, dict):
                continue
            link_req = link.get("req")
            bdd = link.get("bdd")
            if not isinstance(bdd, dict):
                continue
            bdd_scenarios = bdd.get("scenarios", [])
            if not isinstance(bdd_scenarios, list):
                continue
            if scenario.name in bdd_scenarios:
                if has_req_tag and link_req in tags.req:
                    req_bound_in_trace = True
                if has_ctr_tag:
                    # CTR binding: scenario name present in trace.yml bdd 层 +
                    # @CTR tag on scenario suffices (CTR not always in trace.yml schema).
                    ctr_bound_in_trace = True

    messages: list[str] = []
    if not has_req_tag:
        messages.append(f"scenario '{scenario.name}' missing @REQ-NNN tag binding")
    if not has_ctr_tag:
        messages.append(f"scenario '{scenario.name}' missing @CTR-<slug> tag binding")
    if has_req_tag and not req_bound_in_trace:
        messages.append(
            f"scenario '{scenario.name}' has @REQ tag {tags.req} "
            "but not bound in trace.yml bdd 层"
        )

    return TraceResult(
        scenario_name=scenario.name,
        has_req_tag=has_req_tag,
        has_ctr_tag=has_ctr_tag,
        req_bound_in_trace=req_bound_in_trace,
        ctr_bound_in_trace=ctr_bound_in_trace,
        messages=messages,
    )


# ===== Stage E α' E-0a M-FU#4 additive expansion (R-N v18 R-18-2 lock) =====
# 4 NEW additions (3 funcs + 1 const). Section 5 cumulative discipline 守:
# existing 5 funcs (parse_feature_file / extract_tags / load_trace_yml /
# trace_req_ctr / FeatureParseError) + TraceResult shape UNTOUCHED.
#
# Refine 1 (Step 1.5 mini-review):
# - load_runbook + check_justification_fields + JUSTIFICATION_FIELDS are
#   byte-equivalent MIRROR of D-4 G22 check_bdd_unautomated.py local versions
#   (_load_runbook + _check_justification_fields + _JUSTIFICATION_FIELDS).
# - G22 D-4 merged code UNTOUCHED per §7 batch boundary discipline (D-1..D-5
#   merged content immutable).
# - Drift guard test asserts identical semantics until M-FU#10 consolidation
#   (paired-edit warning: BOTH copies must stay identical until consolidated).
#
# Refine 2 (M-FU#10 register):
# - M4-FU-G22-BDD-HELPERS-CONSOLIDATE: post-Stage-E refactor G22 to use
#   bdd_helpers shared versions (M-FU registry 18 → 19 entries).
#
# R-18-6 evidence harness boundary: load_bdd_evidence READS evidence files;
# does NOT generate populated pass_rate data (anti-fabrication per R-16-6
# anti-gate-defeat principle; populated evidence comes from automated
# scenario runs, NOT SDD fabrication).


JUSTIFICATION_FIELDS: tuple[str, ...] = (
    "原因",
    "替代验证手段",
    "升级触发条件",
    "预计时间",
)


def load_runbook(capability_dir: Path) -> str | None:
    """Load runbook.md text;None on missing/error (M-FU#4).

    MIRROR of D-4 G22 ``check_bdd_unautomated._load_runbook`` (validator-local
    there per N-3 D-5;promoted to bdd_helpers per M-FU#4 framework reuse).
    G22 validator NOT touched (§7 batch boundary;D-4 merged preserved).
    Until M-FU#10 consolidation, BOTH copies must stay identical per
    paired-edit warning (drift guard test enforces).
    """
    runbook_path = capability_dir / "runbook.md"
    if not runbook_path.exists():
        return None
    try:
        return runbook_path.read_text(encoding="utf-8")
    except OSError:
        return None


def check_justification_fields(runbook_text: str | None) -> tuple[bool, list[str]]:
    """MVP keyword presence check for 4-field justification (M-FU#4;R-15-1 coupling).

    MIRROR of D-4 G22 ``check_bdd_unautomated._check_justification_fields``
    (validator-local there;promoted to bdd_helpers per M-FU#4 framework reuse).
    G22 validator NOT touched (§7 batch boundary). Same MVP semantic:
    per-scenario sectioning standardized at M-FU#7 Stage E α' completion
    (currently substring check across full runbook body).

    Returns (all_present, missing_fields).
    """
    if runbook_text is None:
        return False, list(JUSTIFICATION_FIELDS)
    missing = [f for f in JUSTIFICATION_FIELDS if f not in runbook_text]
    return len(missing) == 0, missing


def load_bdd_evidence(
    capability_dir: Path, scenario_name: str | None = None
) -> dict | None:
    """Find + load evidence/bdd/*.md frontmatter for a scenario (M-FU#4 primary).

    Per R-N v18 R-18-2 additive expansion + R-15-1 G21+G22 share runbook
    justification source coupling. G21 uses this helper for evidence pass_rate
    primary check;falls back to runbook justification (R-15-1) if evidence
    absent or pass_rate<1.0.

    Search heuristic: glob ``capability_dir/evidence/bdd/*.md`` and parse
    frontmatter via ``_common.frontmatter.parse_frontmatter`` (existing). If
    ``scenario_name`` provided, prefer files whose stem contains keyword
    (sanitized);else return first found with valid ``pass_rate`` field.

    Schema (per bdd-tdd.md L137-150): expects ``pass_rate: float`` + optional
    ``scenario_count`` + ``risk_breakdown`` + ``adapter_coverage``.

    Graceful None (R-N v7 R-1 carryover): no evidence dir / no .md files /
    no parseable frontmatter / no pass_rate field → None. Caller (G21
    validator) handles fallback to runbook justification per R-15-1.

    ★ Evidence harness boundary (R-18-6 + R-13-10): This helper READS
    evidence files;does NOT generate fake pass_rate data (populated evidence
    comes from automated scenario runs OR fallback runbook owner authorship;
    anti-fabrication per R-16-6 anti-gate-defeat principle).
    """
    from scripts.sdd._common.frontmatter import parse_frontmatter

    bdd_dir = capability_dir / "evidence" / "bdd"
    if not bdd_dir.exists():
        return None

    md_files = sorted(bdd_dir.glob("*.md"))
    if not md_files:
        return None

    # Heuristic: prefer files whose stem contains scenario_name keyword
    if scenario_name:
        sanitized = scenario_name.lower().replace(" ", "_")[:30]
        matching = [f for f in md_files if sanitized in f.stem.lower()]
        candidates = matching if matching else md_files
    else:
        candidates = md_files

    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        meta, _ = parse_frontmatter(text)
        if isinstance(meta, dict) and "pass_rate" in meta:
            return meta

    return None


__all__ = [
    "Feature",
    "FeatureParseError",
    "JUSTIFICATION_FIELDS",
    "Scenario",
    "ScenarioTags",
    "TraceResult",
    "check_justification_fields",
    "extract_tags",
    "load_bdd_evidence",
    "load_runbook",
    "load_trace_yml",
    "parse_feature_file",
    "trace_req_ctr",
]
