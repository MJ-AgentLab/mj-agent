"""enforcement_source.py — loader for the typed Codex enforcement source.

`sdd/adapters/codex-enforcement.yml` is the schema-v1 typed source defined by
Epic #499 plan §2.8.7. It is the ONLY input (together with the files it names in
`policy_refs`) from which `.codex/hooks.json` and `.codex/rules/*.rules` may be
derived. This module is the shared loader for it — consumed by BOTH output-class
renderers (`codex_hook_renderer`, `codex_rule_renderer`) and by the runtime
guard, so all three read ONE implementation.

D-017 extended adjacency (`policies/ai-agent.md` §4, A14 row (b)): this is a
loader-class `_common` module for a protected-adjacent typed source, and is
enumerated there next to the PR-A1 lock/Handoff loader. Like that loader it is
deliberately NOT re-exported from `_common/__init__.py`, so the D-017 boundary
stays visible at every import site.

Closed-schema discipline (plan §2.8.7): the top-level key set is CLOSED — no
unknown keys — but not "exact": `config_binding` and `receipt_policy` are
declared-optional at v1 (§5.9 itself calls the config binding "optional", and
§3.3 stages `receipt_policy` to PR-E). Every §2.8 schema that means
all-and-only says "exact keys"; §2.8.7 deliberately says "closed top keys".
Anything unknown, malformed, mis-typed or unsafe fails closed BEFORE any
managed write (AC-06).

Read-only; no secrets; no network; no transcript/assistant-message/private
state. ASCII-only messages.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

ENFORCEMENT_SOURCE_RELPATH = Path("sdd/adapters/codex-enforcement.yml")

SCHEMA_VERSION = 1
# Plan §2.8.7 closed top keys. Closed = no unknown key; see module docstring for
# why this is not the same as the "exact keys" used by §2.8.5/§2.8.6.
TOP_KEYS_REQUIRED = frozenset({"schema_version", "policy_refs", "hooks", "rules"})
TOP_KEYS_OPTIONAL = frozenset({"config_binding", "receipt_policy"})
TOP_KEYS = TOP_KEYS_REQUIRED | TOP_KEYS_OPTIONAL

# Codex 0.147.0 hook event vocabulary (`HookEventNameWire`). Only PreToolUse is
# accepted: it is evaluated BEFORE the tool call runs, which is what plan §5.9
# means by "block before side effect". A PostToolUse deny would be a rollback.
ALLOWED_EVENTS = frozenset({"PreToolUse"})
# Guard surfaces. `path` and `command_arg` are deliberately SEPARATE because
# they answer different questions:
#   command     -- token-prefix match on the shell command itself.
#   path        -- a path this call would WRITE (apply_patch hunk headers, or a
#                  declared file_path/path input). Edit-only surfaces such as
#                  the 4 in-source 必停 files use this.
#   command_arg -- any path-shaped ARGUMENT of a shell command. Reading is
#                  itself the violation only for secrets, so widening every
#                  path guard to shell arguments would wrongly block a harmless
#                  `--rules .codex/rules/mj-agent.rules` read.
ALLOWED_GUARD_SURFACES = frozenset({"command", "path", "command_arg"})
ALLOWED_GUARD_DECISIONS = frozenset({"block"})
# Codex execpolicy decision vocabulary, ordered least -> most strict. codex
# itself aggregates the strictest decision across matched rules and across
# repeated --rules files (verified against codex-cli 0.147.0), so the renderer
# never re-implements precedence.
RULE_DECISIONS = ("allow", "prompt", "forbidden")

RULES_PREFIX = ".codex/rules/"
RULES_SUFFIX = ".rules"


class EnforcementSourceError(Exception):
    """Malformed/unknown/unsafe typed enforcement source — zero managed writes."""


@dataclass(frozen=True)
class Guard:
    guard_id: str
    applies_to: tuple[str, ...]
    decision: str
    deny_patterns: tuple[str, ...]
    reason: str
    # Command prefixes for which this guard does NOT apply. Needed because a
    # path-shaped argument is not always a read: the repo's own documented
    # `docker compose --env-file .env ...` passes the dotenv path to compose
    # rather than reading it into the transcript, and blocking the project's
    # canonical command would make the guard actively wrong.
    exempt_command_prefixes: tuple[str, ...] = ()


@dataclass(frozen=True)
class HookHandler:
    command: tuple[str, ...]
    timeout_seconds: int
    status_message: str | None


@dataclass(frozen=True)
class HookEvent:
    event: str
    matcher: str


@dataclass(frozen=True)
class PrefixRule:
    rule_id: str
    pattern: tuple[str, ...]
    decision: str
    reason: str


@dataclass(frozen=True)
class RuleFile:
    output_path: str
    prefix_rules: tuple[PrefixRule, ...]


@dataclass(frozen=True)
class EnforcementSource:
    schema_version: int
    policy_refs: tuple[str, ...]
    handler: HookHandler
    events: tuple[HookEvent, ...]
    guards: tuple[Guard, ...]
    rule_files: tuple[RuleFile, ...]
    config_binding: Any | None
    receipt_policy: Any | None


def _mapping(node: Any, where: str) -> dict[str, Any]:
    if not isinstance(node, dict):
        raise EnforcementSourceError(f"{where} must be a mapping (got {type(node).__name__})")
    return node


def _closed(node: dict[str, Any], required: frozenset[str], optional: frozenset[str], where: str) -> None:
    actual = set(node)
    missing = required - actual
    if missing:
        # `sorted` on a heterogeneous key set raises TypeError, which would
        # escape as a traceback and break the engine's "never a traceback,
        # always exit 2" contract — so every report sorts by `repr`.
        raise EnforcementSourceError(
            f"{where} missing required key(s): {sorted(missing, key=repr)}"
        )
    unknown = actual - (required | optional)
    if unknown:
        raise EnforcementSourceError(
            f"{where} has unknown key(s) {sorted(unknown, key=repr)} (closed schema)"
        )


def _nonempty_str(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EnforcementSourceError(f"{where} must be a non-empty string (got {value!r})")
    return value


def _str_list(value: Any, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise EnforcementSourceError(f"{where} must be a non-empty list")
    return tuple(_nonempty_str(v, f"{where}[{i}]") for i, v in enumerate(value))


# Glob metacharacters that make a path non-explicit (plan §2.8.4 rejects globs).
# `[` / `]` are deliberately NOT here: this repo's canonical documents are named
# `[TYPE]_Name.md` (e.g. the plan governing this very Epic), so treating brackets
# as glob syntax would make most of the policy corpus undeclarable as a
# `policy_ref`. Every declared ref is opened by `policy_ref_inventory`, so a path
# that does not resolve fails closed regardless.
_GLOB_CHARS = "*?"

# `policy_refs` are read as RAW BYTES and their digests are committed to
# `.agents.lock.json`. Declaring a secret here would therefore make Secrets a
# render input and publish a digest of them — plan §5.9 forbids it absolutely,
# so the loader refuses rather than trusting the author.
_SECRET_REF_PATTERNS = (".env", "config/secrets")


def _safe_repo_relpath(value: str, where: str) -> str:
    """Explicit, repo-relative, POSIX, glob-free path (plan §2.8.4)."""
    if "\\" in value:
        raise EnforcementSourceError(f"{where} must use POSIX slashes (got {value!r})")
    if any(ch in value for ch in _GLOB_CHARS):
        raise EnforcementSourceError(
            f"{where} must be an explicit path, not a glob (got {value!r})"
        )
    if value.startswith("/") or PurePosixPath(value).is_absolute():
        raise EnforcementSourceError(f"{where} must be repo-relative (got {value!r})")
    parts = value.split("/")
    if any(p in ("", ".", "..") for p in parts):
        raise EnforcementSourceError(f"{where} has an empty/'.'/'..' segment (got {value!r})")
    return value


def load_enforcement_source(text: str) -> EnforcementSource:
    """Parse + fully validate the typed source. Raises EnforcementSourceError."""
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:  # pragma: no cover - message varies by libyaml
        raise EnforcementSourceError(f"unparseable YAML: {exc}") from exc
    doc = _mapping(raw, "codex-enforcement.yml root")
    _closed(doc, TOP_KEYS_REQUIRED, TOP_KEYS_OPTIONAL, "codex-enforcement.yml")

    version = doc.get("schema_version")
    if version != SCHEMA_VERSION:
        raise EnforcementSourceError(
            f"schema_version must be {SCHEMA_VERSION} (got {version!r})"
        )

    refs = _str_list(doc.get("policy_refs"), "policy_refs")
    policy_refs = tuple(
        _safe_repo_relpath(r, f"policy_refs[{i}]") for i, r in enumerate(refs)
    )
    for i, ref in enumerate(policy_refs):
        lowered = ref.lower()
        base = lowered.rsplit("/", 1)[-1]
        if base == ".env" or base.startswith(".env.") or any(
            lowered.startswith(p) or ("/" + p) in ("/" + lowered)
            for p in _SECRET_REF_PATTERNS
        ):
            raise EnforcementSourceError(
                f"policy_refs[{i}] {ref!r} names a secret-bearing path; Secrets are"
                " NEVER render inputs (plan §5.9) and their digests must never"
                " reach .agents.lock.json"
            )
    if len(set(policy_refs)) != len(policy_refs):
        raise EnforcementSourceError("policy_refs contains duplicate paths")

    hooks = _mapping(doc.get("hooks"), "hooks")
    _closed(hooks, frozenset({"handler", "events", "guards"}), frozenset(), "hooks")

    handler_node = _mapping(hooks.get("handler"), "hooks.handler")
    _closed(
        handler_node,
        frozenset({"command", "timeout_seconds"}),
        frozenset({"status_message"}),
        "hooks.handler",
    )
    timeout = handler_node.get("timeout_seconds")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 1:
        raise EnforcementSourceError(
            f"hooks.handler.timeout_seconds must be an int >= 1 (got {timeout!r})"
        )
    status_message = handler_node.get("status_message")
    if status_message is not None:
        status_message = _nonempty_str(status_message, "hooks.handler.status_message")
    handler = HookHandler(
        command=_str_list(handler_node.get("command"), "hooks.handler.command"),
        timeout_seconds=timeout,
        status_message=status_message,
    )

    events_raw = hooks.get("events")
    if not isinstance(events_raw, list) or not events_raw:
        raise EnforcementSourceError("hooks.events must be a non-empty list")
    events: list[HookEvent] = []
    for i, node in enumerate(events_raw):
        where = f"hooks.events[{i}]"
        item = _mapping(node, where)
        _closed(item, frozenset({"event", "matcher"}), frozenset(), where)
        event = _nonempty_str(item.get("event"), f"{where}.event")
        if event not in ALLOWED_EVENTS:
            raise EnforcementSourceError(
                f"{where}.event must be one of {sorted(ALLOWED_EVENTS)} (got {event!r})"
            )
        events.append(HookEvent(event=event, matcher=_nonempty_str(item.get("matcher"), f"{where}.matcher")))
    seen_events = {(e.event, e.matcher) for e in events}
    if len(seen_events) != len(events):
        raise EnforcementSourceError("hooks.events has duplicate (event, matcher) pairs")

    guards_raw = hooks.get("guards")
    if not isinstance(guards_raw, list) or not guards_raw:
        raise EnforcementSourceError("hooks.guards must be a non-empty list")
    guards: list[Guard] = []
    for i, node in enumerate(guards_raw):
        where = f"hooks.guards[{i}]"
        item = _mapping(node, where)
        _closed(
            item,
            frozenset({"id", "applies_to", "decision", "deny_patterns", "reason"}),
            frozenset({"exempt_command_prefixes"}),
            where,
        )
        applies_to = _str_list(item.get("applies_to"), f"{where}.applies_to")
        unknown_surfaces = [s for s in applies_to if s not in ALLOWED_GUARD_SURFACES]
        if unknown_surfaces:
            raise EnforcementSourceError(
                f"{where}.applies_to must contain only {sorted(ALLOWED_GUARD_SURFACES)}"
                f" (got {unknown_surfaces!r})"
            )
        if len(set(applies_to)) != len(applies_to):
            raise EnforcementSourceError(f"{where}.applies_to has duplicate surfaces")
        decision = _nonempty_str(item.get("decision"), f"{where}.decision")
        if decision not in ALLOWED_GUARD_DECISIONS:
            raise EnforcementSourceError(
                f"{where}.decision must be one of {sorted(ALLOWED_GUARD_DECISIONS)}"
                f" (got {decision!r})"
            )
        exempt = item.get("exempt_command_prefixes")
        exempt_prefixes = (
            () if exempt is None
            else _str_list(exempt, f"{where}.exempt_command_prefixes")
        )
        guards.append(
            Guard(
                guard_id=_nonempty_str(item.get("id"), f"{where}.id"),
                applies_to=applies_to,
                decision=decision,
                deny_patterns=_str_list(item.get("deny_patterns"), f"{where}.deny_patterns"),
                reason=_nonempty_str(item.get("reason"), f"{where}.reason"),
                exempt_command_prefixes=exempt_prefixes,
            )
        )
    guard_ids = [g.guard_id for g in guards]
    if len(set(guard_ids)) != len(guard_ids):
        raise EnforcementSourceError("hooks.guards has duplicate ids")

    rules_raw = doc.get("rules")
    if not isinstance(rules_raw, list) or not rules_raw:
        raise EnforcementSourceError("rules must be a non-empty list")
    rule_files: list[RuleFile] = []
    for i, node in enumerate(rules_raw):
        where = f"rules[{i}]"
        item = _mapping(node, where)
        _closed(item, frozenset({"output_path", "prefix_rules"}), frozenset(), where)
        out = _safe_repo_relpath(
            _nonempty_str(item.get("output_path"), f"{where}.output_path"),
            f"{where}.output_path",
        )
        # Path grammar is pinned by the lock's codex-rule kind (plan §2.6).
        if not out.startswith(RULES_PREFIX) or not out.endswith(RULES_SUFFIX):
            raise EnforcementSourceError(
                f"{where}.output_path must be '{RULES_PREFIX}<name>{RULES_SUFFIX}'"
                f" (got {out!r})"
            )
        if "/" in out[len(RULES_PREFIX):]:
            raise EnforcementSourceError(
                f"{where}.output_path must not nest below {RULES_PREFIX} (got {out!r})"
            )
        pr_raw = item.get("prefix_rules")
        if not isinstance(pr_raw, list) or not pr_raw:
            # codex itself refuses an empty policy ("rules prefix_rules cannot be empty").
            raise EnforcementSourceError(f"{where}.prefix_rules must be a non-empty list")
        prefix_rules: list[PrefixRule] = []
        for j, rnode in enumerate(pr_raw):
            rwhere = f"{where}.prefix_rules[{j}]"
            ritem = _mapping(rnode, rwhere)
            _closed(
                ritem,
                frozenset({"id", "pattern", "decision", "reason"}),
                frozenset(),
                rwhere,
            )
            decision = _nonempty_str(ritem.get("decision"), f"{rwhere}.decision")
            if decision not in RULE_DECISIONS:
                raise EnforcementSourceError(
                    f"{rwhere}.decision must be one of {list(RULE_DECISIONS)}"
                    f" (got {decision!r})"
                )
            pattern = _str_list(ritem.get("pattern"), f"{rwhere}.pattern")
            if any(tok != tok.strip() or " " in tok for tok in pattern):
                raise EnforcementSourceError(
                    f"{rwhere}.pattern tokens must not contain whitespace (got {list(pattern)!r})"
                )
            prefix_rules.append(
                PrefixRule(
                    rule_id=_nonempty_str(ritem.get("id"), f"{rwhere}.id"),
                    pattern=pattern,
                    decision=decision,
                    reason=_nonempty_str(ritem.get("reason"), f"{rwhere}.reason"),
                )
            )
        ids = [r.rule_id for r in prefix_rules]
        if len(set(ids)) != len(ids):
            raise EnforcementSourceError(f"{where}.prefix_rules has duplicate ids")
        rule_files.append(RuleFile(output_path=out, prefix_rules=tuple(prefix_rules)))
    outs = [r.output_path for r in rule_files]
    if len(set(outs)) != len(outs):
        raise EnforcementSourceError("rules has duplicate output_path values")

    return EnforcementSource(
        schema_version=SCHEMA_VERSION,
        policy_refs=policy_refs,
        handler=handler,
        events=tuple(events),
        guards=tuple(guards),
        rule_files=tuple(rule_files),
        config_binding=doc.get("config_binding"),
        receipt_policy=doc.get("receipt_policy"),
    )


def policy_ref_inventory(repo_root: Path, policy_refs: tuple[str, ...]) -> dict[str, Any]:
    """Build the plan §2.8.4 inventory: {schema_version, files:[{path, raw_sha256}]}.

    `files` is sorted by path and non-empty; a declared file that does not exist
    fails closed. Digests are over RAW bytes with CRLF normalized to LF so a
    Windows checkout and a Linux CI runner agree (the repo's `.gitattributes`
    pins LF on checkout, but an already-CRLF working file must not silently
    change the digest).
    """
    files: list[dict[str, str]] = []
    for ref in sorted(set(policy_refs)):
        target = repo_root / ref
        try:
            raw = target.read_bytes()
        except OSError as exc:
            raise EnforcementSourceError(
                f"declared policy_ref '{ref}' is unreadable: {exc}"
            ) from exc
        files.append(
            {
                "path": ref,
                "raw_sha256": hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(),
            }
        )
    if not files:
        raise EnforcementSourceError("policy_refs inventory is empty")
    return {"schema_version": 1, "files": files}


__all__ = [
    "ENFORCEMENT_SOURCE_RELPATH",
    "EnforcementSource",
    "EnforcementSourceError",
    "Guard",
    "HookEvent",
    "HookHandler",
    "PrefixRule",
    "RULE_DECISIONS",
    "RuleFile",
    "load_enforcement_source",
    "policy_ref_inventory",
]
