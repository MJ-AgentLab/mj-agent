"""skill_renderer.py — the `.agents/skills/**` output-class renderer (dormant v2).

This is the `skill_renderer` module pre-registered in `policies/ai-agent.md`
§4 (A14 row (b), D-017 extended adjacency; ADR-039 — PR-B/D/E surfaces
enrolled ahead of landing). Epic #499 plan §2.4 (translation ownership +
transform model + renderer wire format) and §2.5 (dependency registry, two-layer
source evidence). Dormant until the PR-C1 cutover: the real tree keeps the v1
raw byte-copy path inside `agents_sync.py`; everything here is exercised by
tests and by the PR-P1b production-renderer evidence run.

Contents (one output class — skills):

- strict typed-source loaders for `sdd/workflows/development-agent-workflows.yml`
  (workflow/dependency semantics registry) and
  `sdd/adapters/codex-skill-translation.yml` (harness-primitive disposition
  SoT: versioned lexicon + interaction sites + templates + preface version).
  YAML acceptance per plan §2.8.1: safe scalars/lists/maps only — tags,
  aliases, merge keys, duplicate keys, unknown schema versions and extra keys
  all refuse before any consumer runs.
- layer-A scanner: word-boundary `/mj-agent-*` slash tokens inside the THREE
  scan regions (`## Handoff*` sections — same semantics as the shared
  projection_loader parser; `Sub-skill / Tool Calls` sections; `dot` fenced
  blocks). Everything outside the regions is NOT an automatic edge.
- fail-closed lexicon census over the FULL file (frontmatter included, plan
  §2.4): every hit must carry a category disposition or rendering refuses.

The Handoff-region semantics are the ONE shared implementation extracted at
PR-A1 (`projection_loader.HANDOFF_HEADING`/`HEADING`/`SKILL_REF`) — imported
here, never re-implemented (A1 ledger governance fact 1).

Read-only; no secrets; no network; deterministic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import yaml

from scripts.sdd._common.projection_loader import (
    HANDOFF_HEADING,
    HEADING,
    SKILL_REF,
)

RENDERER_MODULE = "scripts.sdd._common.skill_renderer"
RENDERER_VERSION = 1

WORKFLOW_REGISTRY_RELPATH = "sdd/workflows/development-agent-workflows.yml"
TRANSLATION_MAP_RELPATH = "sdd/adapters/codex-skill-translation.yml"
PREFACE_RELPATH = "sdd/adapters/codex-skill-preface.md"

KNOWN_WORKFLOW_SCHEMA_VERSIONS = frozenset({1})
KNOWN_TRANSLATION_SCHEMA_VERSIONS = frozenset({1})

# Codex truncates skill descriptions for discovery (observed 1024-byte budget,
# Epic #499 F5): a summary that does not fit whole is a defect, fail closed.
DISCOVERY_SUMMARY_MAX_BYTES = 1024

RELATIONS = frozenset({"call", "handoff", "reference"})
ACTIVATIONS = frozenset({"always", "conditional", "owner-gated"})
CLOSURES = frozenset({"carrier-required", "substitute-required", "advisory"})
SUBSTITUTE_KINDS = frozenset(
    {"tool-neutral-command", "inline-procedure", "owner-manual-route",
     "claude-only-by-design"}
)
SITE_DISPOSITIONS = frozenset({"t1a", "t1b", "noop-mention"})
LEXICON_DISPOSITIONS = frozenset(
    {"noop-preface", "site-classified", "region-edge-or-noop", "t3-or-noop"}
)

CAPABILITY_ID = re.compile(r"^mj-agent-[a-z0-9-]+$")
WILDCARD_ID = re.compile(r"^mj-agent-[a-z0-9-]+-\*$")
# Sub-skill region heading (plan §2.5 region 2 — grouped alternation, anchored;
# `## Direct Bash Calls…` is an intentional non-match).
SUBSKILL_HEADING = re.compile(
    r"^#{1,6}\s+(?:Sub-skill(?:\s*/\s*Tool Calls|\s+Calls)?|Tool Calls)(?:\s|$)"
)
ANY_HEADING = re.compile(r"^(#{1,6})\s")


class TranslationError(ValueError):
    """Fail-closed refusal anywhere in the translation domain — write nothing."""


# ------------------------------------------------------------- strict YAML


class _StrictLoader(yaml.SafeLoader):
    """SafeLoader that additionally rejects duplicate keys, aliases and merge
    keys (plan §2.8.1: safe scalar/list/map only)."""

    def compose_node(self, parent: yaml.Node | None, index: int) -> yaml.Node:
        if self.check_event(yaml.events.AliasEvent):
            raise TranslationError(
                "YAML aliases/anchors are not accepted (closed schema)"
            )
        return super().compose_node(parent, index)


def _strict_map(loader: _StrictLoader, node: yaml.MappingNode) -> dict[Any, Any]:
    seen: set[Any] = set()
    for key_node, _value_node in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge":
            raise TranslationError("YAML merge keys are not accepted (closed schema)")
        key = loader.construct_object(key_node, deep=True)
        if isinstance(key, dict | list):
            raise TranslationError("YAML complex mapping keys are not accepted")
        if key in seen:
            raise TranslationError(f"duplicate YAML key {key!r} (closed schema)")
        seen.add(key)
    return dict(loader.construct_pairs(node, deep=True))


_StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _strict_map
)


def strict_yaml_load(text: str) -> Any:
    """Strict YAML for typed sources: rejects tags, aliases, merge keys and
    duplicate keys before any schema validation runs."""
    try:
        node = yaml.compose(text, Loader=_StrictLoader)
    except yaml.YAMLError as exc:
        raise TranslationError(f"typed source is not valid YAML: {exc}") from exc
    if node is None:
        raise TranslationError("typed source is empty")
    _reject_unsafe_nodes(node)
    try:
        data = yaml.load(text, Loader=_StrictLoader)  # noqa: S506 (strict SafeLoader subclass)
    except yaml.YAMLError as exc:
        raise TranslationError(f"typed source is not valid YAML: {exc}") from exc
    return data


_SAFE_TAGS = {
    "tag:yaml.org,2002:map",
    "tag:yaml.org,2002:seq",
    "tag:yaml.org,2002:str",
    "tag:yaml.org,2002:int",
    "tag:yaml.org,2002:float",
    "tag:yaml.org,2002:bool",
    "tag:yaml.org,2002:null",
}


def _reject_unsafe_nodes(node: yaml.Node) -> None:
    if node.tag not in _SAFE_TAGS:
        raise TranslationError(
            f"YAML tag {node.tag!r} is not accepted (safe scalar/list/map only)"
        )
    if isinstance(node, yaml.MappingNode):
        for key_node, value_node in node.value:
            _reject_unsafe_nodes(key_node)
            _reject_unsafe_nodes(value_node)
    elif isinstance(node, yaml.SequenceNode):
        for child in node.value:
            _reject_unsafe_nodes(child)


def _require_keys(node: dict[str, Any], keys: set[str], where: str,
                  optional: set[str] | None = None) -> None:
    optional = optional or set()
    actual = set(node)
    if not keys <= actual or not actual <= (keys | optional):
        raise TranslationError(
            f"{where} keys {sorted(actual)} do not match required {sorted(keys)}"
            + (f" + optional {sorted(optional)}" if optional else "")
            + " (closed schema)"
        )


def _req_str(node: dict[str, Any], key: str, where: str) -> str:
    value = node.get(key)
    if not isinstance(value, str) or not value:
        raise TranslationError(f"{where}.{key} must be a non-empty string")
    return value


# ------------------------------------------------------- workflow registry


@dataclass(frozen=True)
class Substitute:
    kind: str
    route_ref: str | None
    policy_ref: str | None
    rationale: str | None


@dataclass(frozen=True)
class SourceEvidence:
    marker_id: str
    path: str
    marker: str


@dataclass(frozen=True)
class RegistryEdge:
    edge_id: str
    from_id: str
    to_id: str  # capability id or `mj-agent-<x>-*` wildcard
    relation: str
    activation: str
    closure: str
    substitute: Substitute | None
    evidence: SourceEvidence | None  # layer-B declared edges only


@dataclass(frozen=True)
class WorkflowRecord:
    workflow_id: str
    capability_id: str
    codex_discovery_summary: str
    required_trigger_terms: tuple[str, ...]


@dataclass(frozen=True)
class WorkflowRegistry:
    workflows: dict[str, WorkflowRecord]  # by workflow_id
    edges: dict[str, RegistryEdge]  # by edge id
    routes: dict[str, str]  # route_ref -> deterministic route text

    def workflow_for_capability(self, capability_id: str) -> WorkflowRecord | None:
        hits = [w for w in self.workflows.values() if w.capability_id == capability_id]
        if len(hits) > 1:  # loader enforces uniqueness; belt and braces
            raise TranslationError(
                f"capability {capability_id!r} has {len(hits)} workflow records"
            )
        return hits[0] if hits else None

    def edges_from(self, capability_id: str) -> list[RegistryEdge]:
        return sorted(
            (e for e in self.edges.values() if e.from_id == capability_id),
            key=lambda e: e.edge_id,
        )


def load_workflow_registry(text: str) -> WorkflowRegistry:
    data = strict_yaml_load(text)
    if not isinstance(data, dict):
        raise TranslationError("workflow registry top level must be a mapping")
    _require_keys(
        data, {"schema_version", "workflows", "edges", "routes"}, "workflow registry"
    )
    version = data["schema_version"]
    if version not in KNOWN_WORKFLOW_SCHEMA_VERSIONS:
        raise TranslationError(
            f"unknown workflow registry schema_version {version!r}; known:"
            f" {sorted(KNOWN_WORKFLOW_SCHEMA_VERSIONS)}"
        )

    workflows: dict[str, WorkflowRecord] = {}
    caps_seen: set[str] = set()
    if not isinstance(data["workflows"], list) or not data["workflows"]:
        raise TranslationError("workflow registry needs a non-empty workflows list")
    for node in data["workflows"]:
        if not isinstance(node, dict):
            raise TranslationError("workflow record must be a mapping")
        _require_keys(
            node,
            {"workflow_id", "capability_id", "codex_discovery_summary",
             "required_trigger_terms"},
            "workflow record",
        )
        wid = _req_str(node, "workflow_id", "workflow")
        cap = _req_str(node, "capability_id", "workflow")
        if CAPABILITY_ID.fullmatch(cap) is None:
            raise TranslationError(f"workflow {wid!r} capability_id {cap!r} invalid")
        summary = _req_str(node, "codex_discovery_summary", f"workflow {wid!r}")
        if "\n" in summary:
            raise TranslationError(f"workflow {wid!r} summary must be single-line")
        if len(summary.encode("utf-8")) > DISCOVERY_SUMMARY_MAX_BYTES:
            raise TranslationError(
                f"workflow {wid!r} summary exceeds the"
                f" {DISCOVERY_SUMMARY_MAX_BYTES}-byte Codex discovery budget"
            )
        terms = node["required_trigger_terms"]
        if (
            not isinstance(terms, list) or not terms
            or any(not isinstance(t, str) or not t for t in terms)
            or len(set(terms)) != len(terms)
        ):
            raise TranslationError(
                f"workflow {wid!r} required_trigger_terms must be a non-empty"
                " list of unique non-empty strings"
            )
        for term in terms:
            if term not in summary:
                raise TranslationError(
                    f"workflow {wid!r} summary is missing required trigger"
                    f" term {term!r} (source/summary closure)"
                )
        if wid in workflows:
            raise TranslationError(f"duplicate workflow_id {wid!r}")
        if cap in caps_seen:
            raise TranslationError(f"capability {cap!r} has two workflow records")
        caps_seen.add(cap)
        workflows[wid] = WorkflowRecord(
            workflow_id=wid,
            capability_id=cap,
            codex_discovery_summary=summary,
            required_trigger_terms=tuple(terms),
        )

    routes: dict[str, str] = {}
    if not isinstance(data["routes"], list):
        raise TranslationError("workflow registry routes must be a list")
    for node in data["routes"]:
        if not isinstance(node, dict):
            raise TranslationError("route record must be a mapping")
        _require_keys(node, {"route_id", "text"}, "route record")
        rid = _req_str(node, "route_id", "route")
        if rid in routes:
            raise TranslationError(f"duplicate route_id {rid!r}")
        routes[rid] = _req_str(node, "text", f"route {rid!r}")

    edges: dict[str, RegistryEdge] = {}
    if not isinstance(data["edges"], list) or not data["edges"]:
        raise TranslationError("workflow registry needs a non-empty edges list")
    for node in data["edges"]:
        if not isinstance(node, dict):
            raise TranslationError("edge record must be a mapping")
        _require_keys(
            node,
            {"id", "from", "to", "relation", "activation", "closure"},
            "edge record",
            optional={"codex_substitute", "source_evidence"},
        )
        eid = _req_str(node, "id", "edge")
        from_id = _req_str(node, "from", f"edge {eid!r}")
        to_id = _req_str(node, "to", f"edge {eid!r}")
        if CAPABILITY_ID.fullmatch(from_id) is None:
            raise TranslationError(f"edge {eid!r} from {from_id!r} invalid")
        if CAPABILITY_ID.fullmatch(to_id) is None and WILDCARD_ID.fullmatch(to_id) is None:
            raise TranslationError(f"edge {eid!r} to {to_id!r} invalid")
        relation = node["relation"]
        activation = node["activation"]
        closure = node["closure"]
        if relation not in RELATIONS:
            raise TranslationError(f"edge {eid!r} relation {relation!r} invalid")
        if activation not in ACTIVATIONS:
            raise TranslationError(f"edge {eid!r} activation {activation!r} invalid")
        if closure not in CLOSURES:
            raise TranslationError(f"edge {eid!r} closure {closure!r} invalid")
        substitute: Substitute | None = None
        if "codex_substitute" in node:
            sub = node["codex_substitute"]
            if not isinstance(sub, dict):
                raise TranslationError(f"edge {eid!r} codex_substitute must be a mapping")
            kind = sub.get("kind")
            if kind not in SUBSTITUTE_KINDS:
                raise TranslationError(
                    f"edge {eid!r} substitute kind {kind!r} invalid"
                )
            if kind in ("tool-neutral-command", "inline-procedure"):
                _require_keys(sub, {"kind", "route_ref"}, f"edge {eid!r} substitute")
            elif kind == "owner-manual-route":
                _require_keys(
                    sub, {"kind", "route_ref", "policy_ref"}, f"edge {eid!r} substitute"
                )
            else:  # claude-only-by-design
                _require_keys(
                    sub, {"kind", "rationale", "policy_ref"}, f"edge {eid!r} substitute"
                )
            route_ref = sub.get("route_ref")
            if route_ref is not None and route_ref not in routes:
                raise TranslationError(
                    f"edge {eid!r} substitute route_ref {route_ref!r} does not"
                    " resolve to a registry route"
                )
            substitute = Substitute(
                kind=kind,
                route_ref=route_ref,
                policy_ref=sub.get("policy_ref"),
                rationale=sub.get("rationale"),
            )
        evidence: SourceEvidence | None = None
        if "source_evidence" in node:
            ev = node["source_evidence"]
            if not isinstance(ev, dict):
                raise TranslationError(f"edge {eid!r} source_evidence must be a mapping")
            _require_keys(
                ev, {"marker_id", "path", "marker"}, f"edge {eid!r} source_evidence"
            )
            evidence = SourceEvidence(
                marker_id=_req_str(ev, "marker_id", f"edge {eid!r}"),
                path=_req_str(ev, "path", f"edge {eid!r}"),
                marker=_req_str(ev, "marker", f"edge {eid!r}"),
            )
        if eid in edges:
            raise TranslationError(f"duplicate edge id {eid!r}")
        edges[eid] = RegistryEdge(
            edge_id=eid, from_id=from_id, to_id=to_id, relation=relation,
            activation=activation, closure=closure, substitute=substitute,
            evidence=evidence,
        )

    marker_ids = [e.evidence.marker_id for e in edges.values() if e.evidence]
    if len(marker_ids) != len(set(marker_ids)):
        raise TranslationError("duplicate source_evidence marker_id across edges")

    return WorkflowRegistry(workflows=workflows, edges=edges, routes=routes)


# -------------------------------------------------------- translation map


@dataclass(frozen=True)
class LexiconCategory:
    name: str
    patterns: tuple[str, ...]
    disposition: str
    compiled: tuple[re.Pattern[str], ...] = field(compare=False, default=())


@dataclass(frozen=True)
class InteractionSite:
    site_id: str
    capability_id: str
    path: str
    marker: str
    disposition: str  # t1a | t1b | noop-mention
    owner_gate_reason: str | None  # canonical enum, t1a only


@dataclass(frozen=True)
class TranslationMap:
    lexicon: dict[str, LexiconCategory]
    sites: dict[str, InteractionSite]
    templates: dict[str, str]
    preface_template_version: int


REQUIRED_TEMPLATES = frozenset({"t1a", "t1b", "t2a-route", "t2b-route"})


def load_translation_map(text: str) -> TranslationMap:
    data = strict_yaml_load(text)
    if not isinstance(data, dict):
        raise TranslationError("translation map top level must be a mapping")
    _require_keys(
        data,
        {"schema_version", "preface_template_version", "lexicon", "sites",
         "templates"},
        "translation map",
    )
    version = data["schema_version"]
    if version not in KNOWN_TRANSLATION_SCHEMA_VERSIONS:
        raise TranslationError(
            f"unknown translation map schema_version {version!r}; known:"
            f" {sorted(KNOWN_TRANSLATION_SCHEMA_VERSIONS)}"
        )
    preface_version = data["preface_template_version"]
    if isinstance(preface_version, bool) or not isinstance(preface_version, int) \
            or preface_version < 1:
        raise TranslationError("preface_template_version must be an integer >= 1")

    lexicon: dict[str, LexiconCategory] = {}
    if not isinstance(data["lexicon"], list) or not data["lexicon"]:
        raise TranslationError("translation map needs a non-empty lexicon list")
    for node in data["lexicon"]:
        if not isinstance(node, dict):
            raise TranslationError("lexicon category must be a mapping")
        _require_keys(node, {"category", "patterns", "disposition"}, "lexicon category")
        name = _req_str(node, "category", "lexicon")
        disposition = node["disposition"]
        if disposition not in LEXICON_DISPOSITIONS:
            raise TranslationError(
                f"lexicon category {name!r} disposition {disposition!r} invalid"
            )
        patterns = node["patterns"]
        if (
            not isinstance(patterns, list) or not patterns
            or any(not isinstance(p, str) or not p for p in patterns)
        ):
            raise TranslationError(
                f"lexicon category {name!r} patterns must be non-empty strings"
            )
        try:
            compiled = tuple(re.compile(p) for p in patterns)
        except re.error as exc:
            raise TranslationError(
                f"lexicon category {name!r} pattern does not compile: {exc}"
            ) from exc
        if name in lexicon:
            raise TranslationError(f"duplicate lexicon category {name!r}")
        lexicon[name] = LexiconCategory(
            name=name, patterns=tuple(patterns), disposition=disposition,
            compiled=compiled,
        )

    sites: dict[str, InteractionSite] = {}
    if not isinstance(data["sites"], list):
        raise TranslationError("translation map sites must be a list")
    for node in data["sites"]:
        if not isinstance(node, dict):
            raise TranslationError("interaction site must be a mapping")
        _require_keys(
            node,
            {"site_id", "capability_id", "path", "marker", "disposition"},
            "interaction site",
            optional={"owner_gate_reason"},
        )
        sid = _req_str(node, "site_id", "site")
        disposition = node["disposition"]
        if disposition not in SITE_DISPOSITIONS:
            raise TranslationError(
                f"site {sid!r} disposition {disposition!r} invalid"
            )
        reason = node.get("owner_gate_reason")
        if disposition == "t1a":
            if not isinstance(reason, str) or not reason:
                raise TranslationError(
                    f"site {sid!r}: t1a requires owner_gate_reason (canonical enum)"
                )
        elif reason is not None:
            raise TranslationError(
                f"site {sid!r}: owner_gate_reason is t1a-only"
            )
        if sid in sites:
            raise TranslationError(f"duplicate site_id {sid!r}")
        sites[sid] = InteractionSite(
            site_id=sid,
            capability_id=_req_str(node, "capability_id", f"site {sid!r}"),
            path=_req_str(node, "path", f"site {sid!r}"),
            marker=_req_str(node, "marker", f"site {sid!r}"),
            disposition=disposition,
            owner_gate_reason=reason,
        )

    templates_node = data["templates"]
    if not isinstance(templates_node, dict):
        raise TranslationError("translation map templates must be a mapping")
    if set(templates_node) != set(REQUIRED_TEMPLATES):
        raise TranslationError(
            f"templates keys {sorted(templates_node)} must be exactly"
            f" {sorted(REQUIRED_TEMPLATES)}"
        )
    templates = {
        key: _req_str(templates_node, key, "templates") for key in templates_node
    }

    return TranslationMap(
        lexicon=lexicon, sites=sites, templates=templates,
        preface_template_version=preface_version,
    )


# ------------------------------------------------------------ layer-A scan


@dataclass(frozen=True)
class ScanToken:
    region: str  # handoff | subskill | dot
    line_no: int  # 1-based, over the FULL file text (frontmatter included)
    token: str  # capability id or `mj-agent-<x>-*` wildcard (no leading slash)
    line_text: str


def scan_layer_a(text: str) -> list[ScanToken]:
    """Word-boundary `/mj-agent-*` tokens inside the three scan regions
    (plan §2.5 layer A). The Handoff semantics come from the ONE shared
    parser regexes in projection_loader (PR-A1); Sub-skill and `dot` fence
    regions are defined here. Everything else is NOT an automatic edge."""
    out: list[ScanToken] = []
    state: str | None = None
    level = 0
    in_dot = False
    for line_no, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not in_dot and stripped == "```dot":
            in_dot = True
            continue
        if in_dot:
            if stripped == "```":
                in_dot = False
                continue
            for token in SKILL_REF.findall(line):
                out.append(ScanToken("dot", line_no, token, line))
            continue
        m = HEADING.match(line) or ANY_HEADING.match(line)
        if m:
            if HANDOFF_HEADING.match(line):
                state = "handoff"
                level = len(m.group(1))
                continue
            if SUBSKILL_HEADING.match(line):
                state = "subskill"
                level = len(m.group(1))
                continue
            if state is not None and len(m.group(1)) <= level:
                state = None
            continue
        if state is not None:
            for token in SKILL_REF.findall(line):
                out.append(ScanToken(state, line_no, token, line))
    return out


# ---------------------------------------------------------- lexicon census


@dataclass(frozen=True)
class LexiconHit:
    category: str
    disposition: str
    token: str
    line_no: int
    line_text: str


def lexicon_scan(text: str, lexicon: dict[str, LexiconCategory]) -> list[LexiconHit]:
    """Scan the FULL text (frontmatter, body, fenced code, inline code, links —
    plan §2.4) against every lexicon category. Each hit carries its category's
    registered disposition; the renderer refuses any hit it cannot dispose of."""
    hits: list[LexiconHit] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for category in lexicon.values():
            for pattern in category.compiled:
                for m in pattern.finditer(line):
                    hits.append(
                        LexiconHit(
                            category=category.name,
                            disposition=category.disposition,
                            token=m.group(0),
                            line_no=line_no,
                            line_text=line,
                        )
                    )
    return hits


def marker_hit_count(text: str, marker: str) -> int:
    """Verbatim substring occurrence count — the machine anchor for per-site
    overrides and layer-B declared edges (zero or multiple hits are both red)."""
    return text.count(marker)


def expand_wildcard(pattern: str, all_ids: set[str]) -> list[str]:
    """Deterministic wildcard expansion (plan §2.5/§2.8.3): `mj-agent-<x>-*`
    resolves against the manifest capability id set, sorted, non-empty."""
    if WILDCARD_ID.fullmatch(pattern) is None:
        raise TranslationError(f"{pattern!r} is not a wildcard capability pattern")
    prefix = pattern[:-1]
    resolved = sorted(i for i in all_ids if i.startswith(prefix))
    if not resolved:
        raise TranslationError(
            f"wildcard {pattern!r} resolves to no capability (empty expansion"
            " is a defect, not an empty set)"
        )
    return resolved
