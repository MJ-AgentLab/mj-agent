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

import json
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


# ----------------------------------------------------------- translated wire
# Renderer wire format (plan §2.4): opening `---` is the first byte; output
# order frontmatter -> closing delimiter -> Codex preface -> translated body;
# UTF-8 no BOM, LF, exactly one final newline. The frontmatter allowlist and
# fixed key order are `name`, `description`; the emitted description is the
# registry's codex_discovery_summary as a JSON-style double-quoted YAML scalar
# (ensure_ascii=false). Input BOM/CRLF and quoted/folded description forms do
# not influence the output.


@dataclass(frozen=True)
class SourceDocument:
    name: str
    description_raw: str  # verbatim frontmatter description block (unparsed)
    body: str  # LF-normalized body AFTER the closing delimiter
    frontmatter_lines: int  # line count of `---` .. `---` inclusive


_FM_KEY = re.compile(r"^([A-Za-z0-9_-]+):")


def parse_source_document(source_bytes: bytes) -> SourceDocument:
    """Closed frontmatter parse. The live descriptions are plain scalars that
    are NOT loadable YAML (they embed ": "), so this is a line-shape parser:
    exactly `name` then `description`, no duplicates, no extra top-level key.
    Continuation lines of a folded/quoted description must be indented."""
    try:
        text = source_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise TranslationError(f"source is not UTF-8: {exc}") from exc
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise TranslationError("source must open with a `---` frontmatter fence")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise TranslationError("source frontmatter has no closing `---` fence")
    fm_block = text[4:end]
    body = text[end + len("\n---\n"):]
    fm_lines = fm_block.split("\n")
    if not fm_lines or not fm_lines[0].startswith("name:"):
        raise TranslationError("frontmatter must start with the `name` key")
    name = fm_lines[0][len("name:"):].strip()
    if not name:
        raise TranslationError("frontmatter `name` must be a non-empty scalar")
    if len(fm_lines) < 2 or not fm_lines[1].startswith("description:"):
        raise TranslationError(
            "frontmatter must have exactly `name` then `description`"
        )
    description_raw = fm_lines[1][len("description:"):].lstrip()
    for line in fm_lines[2:]:
        if not line:
            continue
        if line[0] not in (" ", "\t"):
            m = _FM_KEY.match(line)
            if m:
                raise TranslationError(
                    f"frontmatter key {m.group(1)!r} is outside the closed"
                    " allowlist (name, description)"
                )
            raise TranslationError(
                "frontmatter description continuation lines must be indented"
            )
        description_raw += "\n" + line
    return SourceDocument(
        name=name,
        description_raw=description_raw,
        body=body,
        frontmatter_lines=fm_block.count("\n") + 3,
    )


def _render_failure(
    capability_id: str, source_path: str, problems: list[tuple[int, str, str, str]]
) -> TranslationError:
    """Fail-closed diagnostic block (plan §2.4): capability, source line text,
    lexicon category/token, map path + expected key, remediation order."""
    lines = [f"translation refused for {capability_id}:"]
    for line_no, category, token, line_text in problems:
        lines.append(f"  source: {source_path}:{line_no}: {line_text.strip()[:100]}")
        lines.append(f"  lexicon category: {category}; token: {token!r}")
        lines.append(
            f"  map: {TRANSLATION_MAP_RELPATH} — add a per-site entry under"
            " `sites:` (unique verbatim marker) or a category disposition"
            " under `lexicon:`"
        )
    lines.append(
        "  remediation order: 1) classify the token in the translation map"
        " (Owner approval: declared-contract-change); 2) or adjust the source"
        " through its own gate; 3) re-run the render."
    )
    return TranslationError("\n".join(lines))


def _fence_state(lines: list[str]) -> list[str | None]:
    """Per-line fence context: None (outside), 'dot', or 'other'."""
    out: list[str | None] = []
    fence: str | None = None
    for line in lines:
        stripped = line.strip()
        if fence is None and stripped.startswith("```") and stripped != "```":
            fence = "dot" if stripped == "```dot" else "other"
            out.append(None)  # the opening fence line itself
            continue
        if fence is None and stripped == "```":
            # An opening bare fence (plain block) — treat as 'other'.
            fence = "other"
            out.append(None)
            continue
        if fence is not None and stripped == "```":
            fence = None
            out.append(None)
            continue
        out.append(fence)
    return out


def _section_end(lines: list[str], start_index: int, fences: list[str | None]) -> int:
    """Index AFTER the last line of the heading-bounded section containing
    `start_index` (next heading outside fences, or EOF)."""
    for i in range(start_index + 1, len(lines)):
        if fences[i] is None and ANY_HEADING.match(lines[i]):
            return i
    return len(lines)


def _construct_end(lines: list[str], index: int, fences: list[str | None]) -> int:
    """Index AFTER the construct containing line `index` (plan §2.4 T2a):
    inside a fence -> after the closing fence; a table line -> after the last
    contiguous table line; a list item -> after that item's line; otherwise ->
    after the contiguous non-blank block."""
    if fences[index] is not None:
        i = index
        while i < len(lines) and lines[i].strip() != "```":
            i += 1
        return min(i + 1, len(lines))
    line = lines[index]
    if line.lstrip().startswith("|"):
        i = index
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            i += 1
        return i
    if re.match(r"^\s*(?:[-*+]\s|\d+\.\s)", line):
        return index + 1
    i = index
    while i < len(lines) and lines[i].strip():
        i += 1
    return i


def _route_text(edge: RegistryEdge, registry: WorkflowRegistry) -> str:
    if edge.substitute is not None and edge.substitute.route_ref is not None:
        return registry.routes[edge.substitute.route_ref]
    if edge.substitute is not None:  # claude-only-by-design
        return f"no completion path on this side: {edge.substitute.rationale}"
    return (
        f"invoke `${edge.to_id}` (native carrier;"
        f" {edge.relation}, {edge.activation})"
    )


def render_translated(
    source_bytes: bytes,
    capability_id: str,
    registry: WorkflowRegistry,
    tmap: TranslationMap,
    preface_template: str,
    carrier_ids: set[str],
) -> str:
    """Deterministic translated render (plan §2.4). Returns canonical text
    (UTF-8 no BOM, LF, exactly one final newline). Fail-closed on any lexicon
    hit without a disposition, any unclassified interaction token, any site
    marker that hits zero or multiple times, and any region token without a
    registry edge."""
    source_path = f".claude/skills/{capability_id}/SKILL.md"
    doc = parse_source_document(source_bytes)
    workflow = registry.workflow_for_capability(capability_id)
    if workflow is None:
        raise TranslationError(
            f"{capability_id} has no workflow record in the registry"
        )

    full_text = "---\n" + f"name: {doc.name}\ndescription: {doc.description_raw}\n" \
        + "---\n" + doc.body
    # ---- interaction sites: resolve markers to full-text line numbers -----
    sites = [s for s in tmap.sites.values() if s.capability_id == capability_id]
    site_by_line: dict[int, InteractionSite] = {}
    for site in sites:
        count = marker_hit_count(full_text, site.marker)
        if count != 1:
            raise TranslationError(
                f"site {site.site_id}: marker hits {count} times in"
                f" {source_path} (need exactly 1)"
            )
        offset = full_text.index(site.marker)
        line_no = full_text[:offset].count("\n") + 1
        if line_no in site_by_line:
            raise TranslationError(
                f"sites {site_by_line[line_no].site_id} and {site.site_id}"
                f" both claim line {line_no}"
            )
        site_by_line[line_no] = site

    # ---- fail-closed lexicon census over the FULL source ------------------
    region_tokens = {
        (t.line_no, t.token) for t in scan_layer_a(full_text)
    }
    region_lines = {t.line_no for t in scan_layer_a(full_text)}
    edges_by_pair = {
        (e.from_id, e.to_id): e for e in registry.edges.values()
    }
    problems: list[tuple[int, str, str, str]] = []
    for hit in lexicon_scan(full_text, tmap.lexicon):
        if hit.disposition == "noop-preface":
            continue
        if hit.disposition == "t3-or-noop":
            continue  # machine rule — rewrite or provenance passthrough
        if hit.disposition == "site-classified":
            if hit.line_no not in site_by_line:
                problems.append(
                    (hit.line_no, hit.category, hit.token, hit.line_text)
                )
            continue
        if hit.disposition == "region-edge-or-noop":
            token = hit.token[1:]  # strip leading slash
            if (
                hit.line_no in region_lines
                and (hit.line_no, token) in region_tokens
                and (capability_id, token) not in edges_by_pair
            ):
                problems.append(
                    (hit.line_no, hit.category, hit.token, hit.line_text)
                )
            continue
    if problems:
        raise _render_failure(capability_id, source_path, problems)

    # ---- body transform ----------------------------------------------------
    body_offset = doc.frontmatter_lines  # body line i (0-based) = full line i+offset+?
    lines = doc.body.split("\n")
    fences = _fence_state(lines)
    emitted_edges: set[str] = set()
    # insertion queue: line-index-after -> list of (sort_key, block_text)
    insertions: dict[int, list[tuple[str, str]]] = {}

    def queue(index: int, sort_key: str, block: str) -> None:
        insertions.setdefault(index, []).append((sort_key, block))

    t3_pattern = re.compile(r"\.claude/skills/(mj-agent-[a-z0-9-]+)/SKILL\.md")

    new_lines: list[str] = []
    for i, line in enumerate(lines):
        full_line_no = i + body_offset + 1

        def _t3(m: re.Match[str]) -> str:
            name = m.group(1)
            if name in carrier_ids:
                return f".agents/skills/{name}/SKILL.md"
            return m.group(0)

        line = t3_pattern.sub(_t3, line)

        # T2a — region tokens on this line
        if full_line_no in region_lines:
            for token_match in list(SKILL_REF.finditer(line)):
                token = token_match.group(1)
                if (full_line_no, token) not in region_tokens:
                    continue
                edge = edges_by_pair.get((capability_id, token))
                if edge is None:
                    continue  # non-edge token (already validated above)
                target_has_carrier = (
                    not edge.to_id.endswith("*") and edge.to_id in carrier_ids
                )
                replacement = (
                    f"${edge.to_id}" if target_has_carrier
                    else f"Codex substitute {edge.edge_id}"
                )
                line = line.replace(f"/{token}", replacement, 1)
                if edge.edge_id not in emitted_edges:
                    emitted_edges.add(edge.edge_id)
                    template = tmap.templates["t2a-route"]
                    block = template.replace("{edge_id}", edge.edge_id).replace(
                        "{route}", _route_text(edge, registry)
                    ).rstrip("\n")
                    queue(_construct_end(lines, i, fences), edge.edge_id, block)
        new_lines.append(line)

    # T2b — layer-B declared edges anchored in THIS source's body
    for edge in registry.edges_from(capability_id):
        if edge.evidence is None or edge.edge_id in emitted_edges:
            continue
        count = marker_hit_count(full_text, edge.evidence.marker)
        if count != 1:
            raise TranslationError(
                f"edge {edge.edge_id}: marker hits {count} times in"
                f" {source_path} (need exactly 1)"
            )
        offset = full_text.index(edge.evidence.marker)
        marker_line_full = full_text[:offset].count("\n") + 1
        marker_index = marker_line_full - body_offset - 1
        if marker_index < 0:
            raise TranslationError(
                f"edge {edge.edge_id}: marker sits in frontmatter — description"
                " routes use the scalar-safe identity, not a body block"
            )
        emitted_edges.add(edge.edge_id)
        template = tmap.templates["t2b-route"]
        block = template.replace("{edge_id}", edge.edge_id).replace(
            "{route}", _route_text(edge, registry)
        ).rstrip("\n")
        queue(
            _construct_end(lines, marker_index, fences), edge.edge_id, block
        )

    # T1 — interaction sites at end of their heading-bounded section
    for line_no, site in sorted(site_by_line.items()):
        if site.disposition == "noop-mention":
            continue
        index = line_no - body_offset - 1
        if index < 0:
            raise TranslationError(
                f"site {site.site_id}: marker sits in frontmatter"
            )
        if site.disposition == "t1a":
            template = tmap.templates["t1a"].replace(
                "{site_id}", site.site_id
            ).replace("{reason}", site.owner_gate_reason or "")
        else:
            template = tmap.templates["t1b"].replace("{site_id}", site.site_id)
        queue(
            _section_end(lines, index, fences),
            f"zz-site-{site.site_id}",
            template.rstrip("\n"),
        )

    # ---- assemble with insertions -----------------------------------------
    out: list[str] = []
    for i, line in enumerate(new_lines):
        for _key, block in sorted(insertions.get(i, [])):
            if out and out[-1] != "":
                out.append("")
            out.append(block)
            out.append("")
        out.append(line)
    for _key, block in sorted(insertions.get(len(new_lines), [])):
        if out and out[-1] != "":
            out.append("")
        out.append(block)
        out.append("")
    body_text = "\n".join(out)

    preface_body = render_preface(preface_template)
    summary_scalar = json.dumps(
        workflow.codex_discovery_summary, ensure_ascii=False
    )
    trimmed_body = body_text.strip("\n")
    rendered = (
        "---\n"
        f"name: {doc.name}\n"
        f"description: {summary_scalar}\n"
        "---\n"
        "\n"
        f"{preface_body}\n"
        "\n"
        f"{trimmed_body}\n"
    )
    # Fixed blank-line budget (goldens pin it): insertion seams never widen
    # beyond one blank line. Fenced content is exempt — runs of blank lines
    # inside fences are source bytes, not seams.
    return _collapse_blank_runs(rendered)


def _collapse_blank_runs(text: str) -> str:
    lines = text.split("\n")
    fences = _fence_state(lines)
    out: list[str] = []
    blank_run = 0
    for i, line in enumerate(lines):
        if line == "" and fences[i] is None:
            blank_run += 1
            if blank_run > 1:
                continue
        else:
            blank_run = 0
        out.append(line)
    return "\n".join(out)


# ------------------------------------------------------- fidelity coverage
# Renderer-generated coverage report (plan §2.7 item 9 / §2.8.5). The
# INDEPENDENT closure check lives in scripts/sdd/check_fidelity_attestations.py
# and re-derives the inventory WITHOUT importing this generator.

COVERAGE_SCHEMA_VERSION = 1
ITEM_KINDS = (
    "heading", "owner-stop", "prohibition", "validator",
    "frontmatter-description", "dependency-route", "level-handler",
    "git-rule", "issue-route",
)
# Deterministic inventory extraction rules (shared VOCABULARY with the
# independent checker; the code is deliberately duplicated there):
INVENTORY_RULES: dict[str, str] = {
    "heading": r"^#{1,6}\s\S",
    "owner-stop": r"OWNER_APPROVAL_REQUIRED|必停",
    "prohibition": r"❌|\*\*不要\*\*",
    "validator": r"scripts/(?:sdd/)?[a-z0-9_]+\.py",
    "level-handler": r"\bLevel [ABC]\b",
    "git-rule": r"\bG[12]\b",
    "issue-route": r"ISSUE_TEMPLATE",
}


def derive_inventory_lines(body: str) -> list[tuple[str, int, str]]:
    """(item_kind, body line no, line text) for every rule hit outside dot/
    generic fences for headings, everywhere for the other kinds."""
    lines = body.split("\n")
    fences = _fence_state(lines)
    out: list[tuple[str, int, str]] = []
    for kind in ITEM_KINDS:
        pattern = INVENTORY_RULES.get(kind)
        if pattern is None:
            continue  # frontmatter-description / dependency-route are not line rules
        compiled = re.compile(pattern)
        for i, line in enumerate(lines):
            if kind == "heading" and fences[i] is not None:
                continue
            if compiled.search(line):
                out.append((kind, i + 1, line))
    return out


def _sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def generate_coverage(
    capability_id: str,
    source_bytes: bytes,
    artifact_text: str,
    registry: WorkflowRegistry,
) -> dict[str, Any]:
    """Machine-generated coverage report (coverage v1, §2.8.5 exact keys).
    Raises when any inventory item has no artifact coverage — a missing item is
    an inventory-closure failure, never a status value."""
    doc = parse_source_document(source_bytes)
    artifact_lines = artifact_text.split("\n")
    items: list[dict[str, Any]] = []
    counters: dict[str, int] = {}

    def _add(kind: str, source_locator: str, source_text: str,
             artifact_locator: str, artifact_text_slice: str,
             transform_class: str, status: str) -> None:
        counters[kind] = counters.get(kind, 0) + 1
        items.append(
            {
                "item_id": f"{kind}-{counters[kind]:03d}",
                "item_kind": kind,
                "source_locator": source_locator,
                "source_sha256": _sha256_text(source_text),
                "artifact_locator": artifact_locator,
                "artifact_sha256": _sha256_text(artifact_text_slice),
                "transform_class": transform_class,
                "status": status,
            }
        )

    for kind, line_no, line in derive_inventory_lines(doc.body):
        stripped = line.strip()
        matches = [
            i + 1 for i, a in enumerate(artifact_lines) if stripped and stripped in a
        ]
        if matches:
            _add(kind, f"body-line:{line_no}", line,
                 f"line:{matches[0]}", stripped, "NOOP", "COVERED")
            continue
        # transformed line: a region token was rewritten to $-form/substitute
        transformed = [
            i + 1 for i, a in enumerate(artifact_lines)
            if "$mj-agent-" in a or "Codex substitute edge-" in a
        ]
        candidates = [
            i for i in transformed
            if SKILL_REF.sub("$X", stripped)[:24] and stripped[:8] in artifact_lines[i - 1]
        ]
        anchor = candidates[0] if candidates else (transformed[0] if transformed else None)
        if anchor is None:
            raise TranslationError(
                f"coverage closure failure: {capability_id} {kind} item at body"
                f" line {line_no} has no artifact coverage: {stripped[:80]!r}"
            )
        _add(kind, f"body-line:{line_no}", line,
             f"line:{anchor}", artifact_lines[anchor - 1], "T2a", "COVERED")

    # frontmatter description — replaced by the registry summary (wire format)
    desc_line = next(
        (i + 1 for i, a in enumerate(artifact_lines) if a.startswith("description: ")),
        None,
    )
    if desc_line is None:
        raise TranslationError(
            f"coverage closure failure: {capability_id} artifact has no"
            " description line"
        )
    _add("frontmatter-description", "frontmatter:description",
         doc.description_raw, f"line:{desc_line}",
         artifact_lines[desc_line - 1], "NOOP", "COVERED")

    for edge in registry.edges_from(capability_id):
        identity = f"<!-- codex-route:{edge.edge_id} -->"
        matches = [
            i + 1 for i, a in enumerate(artifact_lines) if identity in a
        ]
        if len(matches) != 1:
            raise TranslationError(
                f"coverage closure failure: {capability_id} edge"
                f" {edge.edge_id} identity appears {len(matches)} times"
            )
        _add("dependency-route", f"edge:{edge.edge_id}", edge.edge_id,
             f"line:{matches[0]}", identity,
             "T2b" if edge.evidence is not None else "T2a", "COVERED")

    projection = [
        {k: item[k] for k in (
            "item_id", "item_kind", "source_locator", "source_sha256",
            "artifact_locator", "artifact_sha256", "transform_class", "status",
        )}
        for item in items
    ]
    return {
        "schema_version": COVERAGE_SCHEMA_VERSION,
        "capability_id": capability_id,
        "source_path": f".claude/skills/{capability_id}/SKILL.md",
        "artifact_path": f".agents/skills/{capability_id}/SKILL.md",
        "source_sha256": _sha256_text(
            source_bytes.decode("utf-8-sig").replace("\r\n", "\n")
        ),
        "artifact_sha256": _sha256_text(artifact_text),
        "inventory_sha256": _sha256_of_canonical_local(projection),
        "items": projection,
    }


def _sha256_of_canonical_local(obj: Any) -> str:
    import hashlib

    text = json.dumps(
        obj, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
    ) + "\n"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


_HTML_COMMENT = re.compile(r"<!--.*?-->\n?", flags=re.DOTALL)


def render_preface(preface_template: str) -> str:
    """Preface body from the raw template: LF-normalized, template provenance
    comments stripped, no leading/trailing blank lines (the blank-line budget
    around the preface is fixed by the assembly + goldens)."""
    text = preface_template.replace("\r\n", "\n")
    text = _HTML_COMMENT.sub("", text)
    return text.strip("\n")
