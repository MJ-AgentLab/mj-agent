"""scripts/sdd/run_codex_carrier_probe.py — Epic #499 runtime feasibility probe.

Implements the named producer of `plans/[PLAN]_codex_cross_carrier_kernel.md` §2.8.6:
two mutually independent JSON evidence files, never aggregated with each other:

``deterministic-gate-v1``
    Machine-decidable feasibility cases over the 18 required source candidates
    (§2.2.1) in root / nested / worktree and isolated / actual-user-layer layouts
    (§5.4). ``verdict`` is PASS only if every case is PASS; otherwise the highest
    of ``ERROR > FAIL > BLOCKED_PREREQUISITE`` wins. Where Codex exposes no
    reproducible inspection interface a case must report BLOCKED_PREREQUISITE —
    a model answer never impersonates PASS.

``model-telemetry-v1``
    Implicit-trigger observations: per capability x prompt exactly three runs
    (``run_index`` 1-3). Telemetry is metadata only — no transcript, no secrets,
    no chain-of-thought — and it is structurally incapable of altering the
    deterministic verdict (AC-09): this schema has no verdict field at all.

Two delivery units share this producer, selected with ``--unit`` (plan §5.4/§5.6):

``p1a``  candidate carriers are the **raw source blobs** (the production renderer
         did not exist yet). Merge condition was deterministic ``PASS_CANDIDATE``.
``p1b``  candidate carriers are the output of the **exact production renderer /
         module / version** landed by PR-B — ``agents_sync._v2_desired_state`` over
         a derived candidate v2 manifest. Merge condition is deterministic ``PASS``.
         P1b additionally pins renderer-module identity, render determinism and
         per-output exact bytes, and measures the discovery budget against the
         *rendered* description rather than the raw source description.

Design points the plan leaves to the producer (Owner-ratified at Gate 1):

- ``observed_class`` closed enum: ``TRIGGERED_TARGET | TRIGGERED_OTHER |
  NOT_TRIGGERED | UNPARSEABLE``. Classification parses the ``codex exec --json``
  event stream deterministically; it never uses the model's self-report.
- description budget: a candidate PASSes when its frontmatter description reaches
  the fresh-process discovery rendering (``codex debug prompt-input``) in a legal
  shape — complete, or an exact prefix truncation at ``DISCOVERY_BUDGET_CHARS``
  with the ``...`` marker. Oversize is recorded data, not a failure.
- frontmatter description scalars are **unquoted before comparison**: the
  translated renderer emits ``description`` as a JSON-style double-quoted YAML
  scalar, and Codex surfaces the *parsed* value. Comparing the quoted literal
  against the surfaced value would report a spurious ``malformed`` (PR-P1b Stage 3).
  No raw source uses a quoted description, so P1a semantics are unchanged.
- raw captures (prompt-input JSON, mcp list output, exec event streams) stay in
  the gitignored local dir; the tracked evidence files carry digests only, so
  user-layer configuration details never enter the repository.

Candidate bytes are taken from the **git blob** (``git show <rev>:<path>``), never
the worktree file: `.gitattributes` makes Windows checkouts CRLF while the blob
is LF, and a worktree-byte identity could not be reproduced on Linux CI. P1b
therefore materializes the render inputs as blob bytes into a temporary tree and
renders from there, so every published candidate digest is machine-independent
(the byte-copy output class is raw-bytes-v1, i.e. EOL-sensitive — plan follow-up F9).

Canonicalization follows plan §2.8.1 (canonical JSON, RFC 3339 UTC seconds,
run ID ``<schema>-<YYYYMMDDTHHMMSSZ>-<head12>``, fail-closed on an existing
output path) and §2.7 (set digest = SHA-256 over the canonical JSON object
``path -> raw_sha256`` with code-point-sorted keys).

Subcommands:

``emit-fixtures``   pin the probed revision's expected values into the tracked
                    per-unit fixture file (authoring step; committed with the probe).
``deterministic``   run the deterministic gate; write one evidence JSON.
``telemetry``       run the model-telemetry leg; write one evidence JSON.

``--rev`` pins the probed revision explicitly (default ``HEAD``). P1b targets the
frozen PR-B merge commit, which stops being ``HEAD`` as soon as the evidence branch
takes its first commit, so the target must be stated rather than inferred.

Exit codes: 0 = producer ran and wrote evidence (the verdict may still be FAIL —
read the file); 2 = producer could not run at all (missing fixture, output
collision, malformed inputs). A missing prerequisite inside a case is that
case's BLOCKED_PREREQUISITE, not an exit-2.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NamedTuple, NoReturn

import yaml

# The P1b leg imports the PRODUCTION renderer modules by package path; put the
# worktree root on sys.path the same way every other scripts/sdd entry point does.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

EPIC_ID = 499
UNIT_ID = "PR-P1a"

# Delivery unit selector (plan §5.4 / §5.6). Each unit owns its own fixture file
# so a re-emit never mutates an already-published unit's expected values.
UNITS: tuple[str, ...] = ("p1a", "p1b")
UNIT_LABELS = {"p1a": "PR-P1a", "p1b": "PR-P1b"}

DET_SCHEMA = "deterministic-gate-v1"
TEL_SCHEMA = "model-telemetry-v1"

DEFAULT_OUT_DIR = Path("evidence/development-agent-v8/probe")
DEFAULT_LOCAL_DIR = Path(".mj-agent-local/probe")
FIXTURE_NAME = "deterministic-expected.json"
P1B_FIXTURE_NAME = "p1b-deterministic-expected.json"
FIXTURE_NAMES = {"p1a": FIXTURE_NAME, "p1b": P1B_FIXTURE_NAME}
CORPUS_NAME = "prompt-corpus.json"
FIXTURES_SUBDIR = "fixtures"

MANIFEST_PATH = "sdd/development-agent.yml"
SOURCE_ROOT = ".claude/skills"
ARTIFACT_ROOT = ".agents/skills"

# Transcribed from plan §2.2.1 (canonical 18-carrier matrix, code-point sorted).
BYTE_COPY_5: tuple[str, ...] = (
    "mj-agent-flow-diagnose",
    "mj-agent-git-commit",
    "mj-agent-git-delete",
    "mj-agent-git-push",
    "mj-agent-git-sync",
)
TRANSLATED_13: tuple[str, ...] = (
    "mj-agent-doc-validate",
    "mj-agent-flow-implement",
    "mj-agent-flow-intake",
    "mj-agent-flow-plan",
    "mj-agent-flow-post-merge",
    "mj-agent-flow-repo-scan",
    "mj-agent-flow-review-respond",
    "mj-agent-flow-scope-drift",
    "mj-agent-flow-self-review",
    "mj-agent-flow-verify",
    "mj-agent-git-branch",
    "mj-agent-git-issue",
    "mj-agent-git-pr",
)
REQUIRED_18: tuple[str, ...] = tuple(sorted(BYTE_COPY_5 + TRANSLATED_13))

OBSERVED_CLASSES = ("TRIGGERED_TARGET", "TRIGGERED_OTHER", "NOT_TRIGGERED", "UNPARSEABLE")
CASE_STATUSES = ("PASS", "FAIL", "BLOCKED_PREREQUISITE", "ERROR")
VERDICT_PRIORITY = ("ERROR", "FAIL", "BLOCKED_PREREQUISITE")

REPETITIONS = 3
EXEC_TIMEOUT_SECONDS = 180
INSPECT_TIMEOUT_SECONDS = 120

# Environment names allowed into the codex child process. Values are copied from
# the parent only for these names; nothing is ever logged. Credential-bearing
# names are excluded by not being listed — CODEX_HOME is set explicitly per run.
CHILD_ENV_ALLOWLIST: tuple[str, ...] = (
    "PATH",
    "SYSTEMROOT",
    "SYSTEMDRIVE",
    "COMSPEC",
    "WINDIR",
    "TEMP",
    "TMP",
    "USERPROFILE",
    "HOMEDRIVE",
    "HOMEPATH",
    "APPDATA",
    "LOCALAPPDATA",
    "PROGRAMFILES",
    "PROGRAMFILES(X86)",
    "PROGRAMDATA",
    "NUMBER_OF_PROCESSORS",
    "PROCESSOR_ARCHITECTURE",
    "OS",
    "PATHEXT",
    "HOME",
    "LANG",
    "TERM",
)


# --------------------------------------------------------------------------- #
# canonicalization (plan §2.8.1 / §2.7)
# --------------------------------------------------------------------------- #


def canonical_json_bytes(obj: Any) -> bytes:
    """UTF-8, no BOM, LF, 2-space indent, ensure_ascii=false, sorted keys, one final newline."""
    text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)
    return (text + "\n").encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _die(message: str) -> NoReturn:
    """Fail closed: message to stderr, exit status 2 — never 0 and never a bare
    string SystemExit (which Python maps to status 1)."""
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def _strict_json_loads(raw: bytes, what: str) -> Any:
    """JSON load that rejects duplicate keys (plan §2.8.1) and dies closed."""

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out:
                _die(f"duplicate key {key!r} in {what}")
            out[key] = value
        return out

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _die(f"malformed {what}: {exc}")


def digest_of(obj: Any) -> str:
    return sha256_hex(canonical_json_bytes(obj))


def set_digest(path_to_sha: Mapping[str, str]) -> str:
    """Plan §2.7 wire: canonical JSON object path -> raw_sha256, code-point-sorted keys."""
    return digest_of({path: path_to_sha[path] for path in sorted(path_to_sha)})


def utc_now_rfc3339() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_run_id(schema: str, started_at: str, head_sha: str) -> str:
    stamp = started_at.replace("-", "").replace(":", "")
    return f"{schema}-{stamp}-{head_sha[:12]}"


# --------------------------------------------------------------------------- #
# git helpers
# --------------------------------------------------------------------------- #


class GitError(RuntimeError):
    pass


def _git(repo_root: Path, *args: str) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        timeout=120,
    )
    if proc.returncode != 0:
        raise GitError(f"git {' '.join(args[:2])} failed: rc={proc.returncode}")
    return proc.stdout


def resolve_rev(repo_root: Path, rev: str) -> str:
    """Full commit SHA for an explicit revision. P1b probes the frozen PR-B merge
    commit, which is no longer HEAD once the evidence branch takes a commit."""
    return _git(repo_root, "rev-parse", f"{rev}^{{commit}}").decode().strip()


def git_head(repo_root: Path) -> str:
    return _git(repo_root, "rev-parse", "HEAD").decode("ascii").strip()


def git_blob_bytes(repo_root: Path, rev: str, rel_path: str) -> bytes:
    return _git(repo_root, "show", f"{rev}:{rel_path}")


# --------------------------------------------------------------------------- #
# codex runner (injectable for tests)
# --------------------------------------------------------------------------- #


class RunResult(NamedTuple):
    returncode: int
    stdout: bytes
    stderr: bytes


CodexRunner = Callable[[list[str], Path | None, Mapping[str, str], int, bytes | None], RunResult]


def default_codex_runner(
    argv: list[str],
    cwd: Path | None,
    env: Mapping[str, str],
    timeout: int,
    stdin: bytes | None = None,
) -> RunResult:
    try:
        proc = subprocess.run(
            argv,
            cwd=str(cwd) if cwd is not None else None,
            env=dict(env),
            input=stdin,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return RunResult(-1, exc.stdout or b"", (exc.stderr or b"") + b"\n<TIMEOUT>")
    except OSError as exc:
        return RunResult(-2, b"", str(exc).encode("utf-8", "replace"))
    return RunResult(proc.returncode, proc.stdout, proc.stderr)


def sanitized_child_env(parent_env: Mapping[str, str], codex_home: str | None) -> dict[str, str]:
    child: dict[str, str] = {}
    for name in CHILD_ENV_ALLOWLIST:
        value = parent_env.get(name)
        if value is not None:
            child[name] = value
    if codex_home is not None:
        child["CODEX_HOME"] = codex_home
    return child


# --------------------------------------------------------------------------- #
# frontmatter / discovery parsing
# --------------------------------------------------------------------------- #


_FRONT_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):[ \t]?(.*)$")


def parse_frontmatter(blob: bytes) -> dict[str, Any] | None:
    """Parse the leading 2-field frontmatter of a SKILL.md blob; None when malformed.

    Deliberately line-based, not ``yaml.safe_load``: real skill descriptions are
    plain scalars containing ``": "`` (e.g. "Do not use for: ..."), which strict
    YAML rejects but both harness loaders accept. A line starting a new
    ``key: value`` pair opens that key; any other non-empty line continues the
    previous value (joined with a single space), mirroring discovery rendering.
    """
    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    data: dict[str, Any] = {}
    current: str | None = None
    for line in text[4:end].split("\n"):
        match = _FRONT_KEY_RE.match(line)
        if match:
            current = match.group(1)
            data[current] = match.group(2).strip()
        elif line.strip() and current is not None:
            data[current] = f"{data[current]} {line.strip()}"
        elif line.strip():
            return None
    return data or None


def extract_prompt_input_text(raw: bytes) -> str | None:
    """Join every text block of a `codex debug prompt-input` JSON capture."""
    try:
        items = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(items, list):
        return None
    parts: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        for chunk in item.get("content") or []:
            if isinstance(chunk, dict) and isinstance(chunk.get("text"), str):
                parts.append(chunk["text"])
    return "\n".join(parts)


_SKILL_ENTRY_RE = re.compile(r"^- (mj-agent-[a-z0-9-]+): ", re.M)

# Measured on codex-cli 0.147.0 (two independent runs, byte-identical): discovery
# renders each skill description on one line and truncates it deterministically to
# exactly this many characters, replacing the tail with "...". Owner-ratified as
# the det-05 mechanism contract; a future codex changing the budget flips det-05.
DISCOVERY_BUDGET_CHARS = 1024


def discovered_skill_names(prompt_text: str) -> tuple[str, ...]:
    return tuple(sorted(set(_SKILL_ENTRY_RE.findall(prompt_text))))


def discovery_entry_body(prompt_text: str, capability_id: str) -> str | None:
    """One capability's rendered description line, without the ``(file: ...)`` locator."""
    match = re.search(rf"^- {re.escape(capability_id)}: (.*)$", prompt_text, re.M)
    if not match:
        return None
    return re.sub(r" \(file: [^)]*\)$", "", match.group(1))


def classify_render_mode(description: str, body: str) -> str:
    """Deterministic legality classes for the discovery rendering of a description."""
    if body == description:
        return "complete"
    if (
        len(body) == DISCOVERY_BUDGET_CHARS
        and body.endswith("...")
        and description.startswith(body[:-3])
    ):
        return "truncated"
    return "malformed"


def predicted_render_mode(description: str) -> str:
    return "complete" if len(description) <= DISCOVERY_BUDGET_CHARS else "truncated"


def unquote_frontmatter_scalar(raw: str) -> str:
    """The description VALUE behind a frontmatter scalar literal.

    The translated renderer emits ``description`` as a JSON-style double-quoted
    YAML scalar; Codex's loader surfaces the *parsed* value, so comparing the
    quoted literal against the discovery rendering would report a spurious
    ``malformed`` (PR-P1b Stage 3 finding). Plain scalars — every raw
    ``.claude/skills`` source — are returned unchanged, so P1a semantics are
    untouched. A literal that opens and closes with a quote but does not decode
    is left alone rather than guessed at.
    """
    if len(raw) >= 2 and raw.startswith('"') and raw.endswith('"'):
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError:
            return raw
        if isinstance(decoded, str):
            return decoded
    return raw


def frontmatter_description(blob: bytes) -> str | None:
    """Parsed description value of a SKILL.md blob, or None when unusable."""
    front = parse_frontmatter(blob)
    if front is None:
        return None
    raw = front.get("description")
    if not isinstance(raw, str):
        return None
    return unquote_frontmatter_scalar(raw)


# --------------------------------------------------------------------------- #
# path safety (plan §2.1 / §2.8.1)
# --------------------------------------------------------------------------- #

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def derived_artifact_path(capability_id: str) -> str:
    return f"{ARTIFACT_ROOT}/{capability_id}/SKILL.md"


def path_safety_violations(capability_id: str) -> list[str]:
    problems: list[str] = []
    if not _ID_RE.match(capability_id):
        problems.append("ID_SYNTAX")
    rel = derived_artifact_path(capability_id)
    if unicodedata.normalize("NFC", rel) != rel:
        problems.append("NOT_NFC")
    parts = rel.split("/")
    if any(part in ("", ".", "..") for part in parts):
        problems.append("BAD_SEGMENT")
    if "\\" in rel or ":" in rel or rel.startswith("/"):
        problems.append("ABSOLUTE_OR_DRIVE")
    return problems


# --------------------------------------------------------------------------- #
# staging: candidate project layouts
# --------------------------------------------------------------------------- #


class StagedLayout(NamedTuple):
    root: Path
    nested: Path
    worktree: Path
    home_empty: Path
    home_trusted: Path
    candidate_shas: dict[str, str]  # capability id -> raw sha256 of staged bytes


def _run_git_in(cwd: Path, *args: str) -> None:
    proc = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        timeout=120,
    )
    if proc.returncode != 0:
        raise GitError(
            f"staging git {' '.join(args[:3])} failed: "
            + proc.stderr.decode("utf-8", "replace")[:300]
        )


def stage_candidate_project(
    repo_root: Path,
    head_sha: str,
    stage_parent: Path,
    capability_ids: Iterable[str] = REQUIRED_18,
    artifacts: Mapping[str, bytes] | None = None,
    prefix: str = "p1a-stage-",
) -> StagedLayout:
    """Materialize the 18 candidate artifacts into a fresh git project with nested
    dir + linked worktree, plus two isolated CODEX_HOME dirs.

    ``artifacts`` (P1b) supplies exact production-rendered bytes keyed by repo
    relpath — the carriers Codex will actually load after cutover. Without it
    (P1a) the candidates are the raw source git-blob bytes.
    """
    stage_parent.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix=prefix, dir=str(stage_parent)))
    candidate_shas: dict[str, str] = {}
    if artifacts is not None:
        for relpath, data in artifacts.items():
            target = root / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            if relpath.startswith(f"{ARTIFACT_ROOT}/"):
                candidate_shas[relpath.split("/")[2]] = sha256_hex(data)
        return _finish_stage(root, candidate_shas)
    for cid in capability_ids:
        try:
            blob = git_blob_bytes(repo_root, head_sha, f"{SOURCE_ROOT}/{cid}/SKILL.md")
        except GitError:
            # A missing source is a finding, not a staging crash: det-02 reports it
            # and the staged discovery case fails on the absent candidate.
            continue
        target = root / ARTIFACT_ROOT / cid / "SKILL.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
        candidate_shas[cid] = sha256_hex(blob)
    return _finish_stage(root, candidate_shas)


def _finish_stage(root: Path, candidate_shas: dict[str, str]) -> StagedLayout:
    """Turn a directory of staged carriers into the full probe layout: nested cwd,
    linked worktree, and two isolated CODEX_HOME dirs (trust-less vs trusted)."""
    (root / "AGENTS.md").write_bytes(
        b"# staged candidate project (Epic #499 probe fixture)\n\n"
        b"Synthetic layout; carries the required candidate carriers only.\n"
    )
    nested = root / "nested" / "inner"
    nested.mkdir(parents=True)
    (nested / "README.md").write_bytes(b"nested cwd marker\n")

    _run_git_in(root, "init", "-q")
    _run_git_in(root, "config", "user.email", "probe@localhost")
    _run_git_in(root, "config", "user.name", "carrier-probe")
    _run_git_in(root, "config", "core.autocrlf", "false")
    _run_git_in(root, "add", "-A")
    _run_git_in(root, "commit", "-q", "-m", "stage candidates")
    worktree = root.parent / (root.name + "-wt")
    _run_git_in(root, "worktree", "add", "-q", str(worktree), "-b", "probe-wt")

    home_empty = root.parent / (root.name + "-home-empty")
    home_trusted = root.parent / (root.name + "-home-trusted")
    home_empty.mkdir()
    home_trusted.mkdir()
    trust_lines = []
    for project in (root, worktree):
        trust_lines.append(f"[projects.'{project}']\ntrust_level = \"trusted\"\n")
    (home_trusted / "config.toml").write_text("\n".join(trust_lines), encoding="utf-8")
    return StagedLayout(root, nested, worktree, home_empty, home_trusted, candidate_shas)


def write_project_codex_config(root: Path, server_name: str) -> str:
    """Give the staged project a one-server .codex/config.toml canary (no secrets)."""
    cfg_dir = root / ".codex"
    cfg_dir.mkdir(exist_ok=True)
    body = (
        f"[mcp_servers.{server_name}]\n"
        'command = "cmd"\n'
        'args = ["/c", "exit", "0"]\n'
    )
    (cfg_dir / "config.toml").write_text(body, encoding="utf-8")
    return body


# --------------------------------------------------------------------------- #
# case engine
# --------------------------------------------------------------------------- #


class CaseRecorder:
    """Accumulates §2.8.6 case dicts and mirrors raw captures into the local dir."""

    def __init__(self, local_dir: Path, codex_build: str) -> None:
        self.cases: list[dict[str, Any]] = []
        self.local_dir = local_dir
        self.codex_build = codex_build
        self.local_dir.mkdir(parents=True, exist_ok=True)

    def capture(self, name: str, data: bytes) -> str:
        path = self.local_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return sha256_hex(data)

    def add(
        self,
        case_id: str,
        capability_id: str | None,
        surface: str,
        fixture_id: str,
        fixture_sha256: str,
        config_obj: Any,
        expected_sha256: str,
        actual_sha256: str,
        status: str,
        evidence_sha256: str,
        reason_code: str,
    ) -> None:
        if status not in CASE_STATUSES:
            raise ValueError(f"invalid status {status}")
        self.cases.append(
            {
                "case_id": case_id,
                "capability_id": capability_id,
                "surface": surface,
                "fixture_id": fixture_id,
                "fixture_sha256": fixture_sha256,
                "config_sha256": digest_of(config_obj),
                "tool_version": self.codex_build,
                "expected_sha256": expected_sha256,
                "actual_sha256": actual_sha256,
                "status": status,
                "evidence_sha256": evidence_sha256,
                "reason_code": reason_code,
            }
        )

    def verdict(self) -> str:
        statuses = {case["status"] for case in self.cases}
        for level in VERDICT_PRIORITY:
            if level in statuses:
                return level
        return "PASS"


def _match_case(expected_obj: Any, actual_obj: Any) -> tuple[str, str, str]:
    expected_sha = digest_of(expected_obj)
    actual_sha = digest_of(actual_obj)
    status = "PASS" if expected_sha == actual_sha else "FAIL"
    return expected_sha, actual_sha, status


# --------------------------------------------------------------------------- #
# deterministic leg
# --------------------------------------------------------------------------- #


def load_manifest_required_ids(repo_root: Path) -> tuple[str, ...]:
    data = yaml.safe_load((repo_root / MANIFEST_PATH).read_text(encoding="utf-8"))
    ids = [
        cap["id"]
        for cap in data.get("capabilities", [])
        if isinstance(cap, dict) and cap.get("required") is True
    ]
    return tuple(sorted(ids))


def codex_version(runner: CodexRunner, codex_bin: str, env: Mapping[str, str]) -> str | None:
    result = runner([codex_bin, "--version"], None, env, 60, None)
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", "replace").strip() or None


def run_prompt_input(
    runner: CodexRunner,
    codex_bin: str,
    cwd: Path,
    env: Mapping[str, str],
) -> RunResult:
    return runner(
        [codex_bin, "debug", "prompt-input"],
        cwd,
        env,
        INSPECT_TIMEOUT_SECONDS,
        None,
    )


def run_mcp_list(
    runner: CodexRunner,
    codex_bin: str,
    cwd: Path,
    env: Mapping[str, str],
) -> RunResult:
    return runner([codex_bin, "mcp", "list", "--json"], cwd, env, INSPECT_TIMEOUT_SECONDS, None)


def parse_user_trust_entries(config_text: str) -> list[tuple[str, str]]:
    """``(project path, trust_level)`` pairs from the ``[projects]`` table only.

    Reads the section headers plus each section's ``trust_level`` line; every
    other section and value in the user config is never inspected. A section
    header alone is NOT trust — codex records untrusted decisions in the same
    table, so the level must be read and must equal "trusted".
    """
    entries: list[list[str]] = []
    in_projects = False
    for line in config_text.splitlines():
        header = re.match(r"^\[projects\.(?:'([^']+)'|\"([^\"]+)\")\]\s*$", line)
        if header:
            entries.append([header.group(1) or header.group(2) or "", ""])
            in_projects = True
            continue
        if line.lstrip().startswith("["):
            in_projects = False
            continue
        if in_projects and entries:
            level = re.match(r"^\s*trust_level\s*=\s*\"([^\"]*)\"", line)
            if level:
                entries[-1][1] = level.group(1)
    return [(path, lvl) for path, lvl in entries]


def trust_entry_covering(entries: Iterable[tuple[str, str]], project_root: Path) -> str | None:
    root_cmp = str(project_root).replace("/", "\\").lower().rstrip("\\")
    for raw, level in entries:
        if level != "trusted":
            continue
        cleaned = raw.replace("/", "\\").removeprefix("\\\\?\\").lower().rstrip("\\")
        if root_cmp == cleaned or root_cmp.startswith(cleaned + "\\"):
            return raw
    return None


def _record_p1b_cases(
    rec: CaseRecorder,
    fixture: dict[str, Any],
    fixture_id: str,
    fixture_sha: str,
    render: CandidateRender,
) -> None:
    """The PR-P1b exact-byte family (plan §5.6 / §6.2 "production renderer
    exact-byte"). Every case compares the live render against the committed
    fixture; none of them calls Codex."""
    # det-11: the candidate v2 manifest is schema-valid under the production V8
    # object-level checks (top-level shape + DA090-096 carrier schema + posture).
    expected_sha, actual_sha, status = _match_case([], render.manifest_violations)
    rec.add(
        "det-11-candidate-manifest-v2-schema", None, "config", fixture_id, fixture_sha,
        {"probe": "check_development_agent object-level", "schema_version": 2},
        expected_sha, actual_sha, status,
        digest_of(render.manifest_violations),
        "OK" if status == "PASS" else "CANDIDATE_MANIFEST_INVALID",
    )

    # det-12: the renderer modules that actually executed are byte-equal to the
    # modules frozen at the probed commit, at the pinned RENDERER_VERSION.
    # Union, not just the observed set: a module that DROPS OUT of the pipeline
    # would otherwise emit zero cases and leave the verdict green.
    expected_modules: dict[str, Any] = fixture.get("renderer_modules") or {}
    for module_name in sorted(set(render.renderer_identity) | set(expected_modules)):
        observed = render.renderer_identity.get(module_name)
        expected = expected_modules.get(module_name)
        matches_blob = (
            observed is not None
            and observed["imported_sha256"] == observed["blob_sha256"]
        )
        expected_sha, actual_sha, status = _match_case(expected, observed)
        if status == "PASS" and not matches_blob:
            status = "FAIL"
        rec.add(
            f"det-12-renderer-identity--{module_name}", None, "config",
            fixture_id, fixture_sha,
            {"probe": "renderer-module-identity", "module": module_name},
            expected_sha, actual_sha, status,
            digest_of(observed),
            "OK" if status == "PASS" else (
                "RENDERER_MODULE_ABSENT" if observed is None
                else "RENDERER_MODULE_NOT_FROZEN" if not matches_blob
                else "RENDERER_IDENTITY_MISMATCH"
            ),
        )

    # det-13: every candidate output reproduces its pinned bytes, exactly.
    expected_outputs: dict[str, Any] = fixture.get("candidate_output_sha256") or {}
    for path in sorted(set(render.outputs) | set(expected_outputs)):
        data = render.outputs.get(path)
        actual = sha256_hex(data) if data is not None else digest_of(None)
        expected = expected_outputs.get(path)
        status = "PASS" if data is not None and expected == actual else "FAIL"
        entry = render.entries.get(path) or {}
        capability = (
            path.split("/")[2] if path.startswith(f"{ARTIFACT_ROOT}/") else None
        )
        rec.add(
            f"det-13-render-exact-byte--{path}", capability, candidate_surface(entry),
            fixture_id, fixture_sha,
            {"probe": "production-render", "entry_kind": entry.get("entry_kind")},
            expected or digest_of(None), actual, status,
            actual,
            "OK" if status == "PASS" else (
                "CANDIDATE_OUTPUT_MISSING" if data is None
                else "CANDIDATE_DIGEST_MISMATCH"
            ),
        )

    # det-14: two independent renders of the same inputs are byte-identical.
    expected_sha, actual_sha, status = _match_case(True, render.deterministic)
    rec.add(
        "det-14-render-determinism", None, "config", fixture_id, fixture_sha,
        {"probe": "double-render", "outputs": len(render.outputs)},
        expected_sha, actual_sha, status,
        digest_of({"outputs": sorted(render.outputs)}),
        "OK" if status == "PASS" else "RENDER_NON_DETERMINISTIC",
    )

    # det-15: the candidate set digest — the immutable handle PR-C0 binds its
    # fidelity review to and PR-C1 must reproduce.
    output_shas = {path: sha256_hex(data) for path, data in render.outputs.items()}
    expected_sha, actual_sha, status = _match_case(
        fixture.get("candidate_set_sha256"), set_digest(output_shas)
    )
    rec.add(
        "det-15-candidate-set-digest", None, "skill", fixture_id, fixture_sha,
        {"probe": "set-digest", "wire": "plan 2.7"},
        expected_sha, actual_sha, status,
        set_digest(output_shas),
        "OK" if status == "PASS" else "CANDIDATE_SET_DIGEST_MISMATCH",
    )

    # det-16: the derived carrier partition equals the plan §2.2.1 matrix, is
    # disjoint, and covers the required set. Derived — never a hardcoded count.
    observed_partition = render.partition
    union = sorted(observed_partition["byte-copy"] + observed_partition["translated"])
    overlap = sorted(
        set(observed_partition["byte-copy"]) & set(observed_partition["translated"])
    )
    observed_shape = {
        "partition": observed_partition,
        "union": union,
        "overlap": overlap,
    }
    expected_shape = {
        "partition": {
            "byte-copy": sorted(BYTE_COPY_5),
            "translated": sorted(TRANSLATED_13),
        },
        "union": list(REQUIRED_18),
        "overlap": [],
    }
    expected_sha, actual_sha, status = _match_case(expected_shape, observed_shape)
    rec.add(
        "det-16-carrier-partition", None, "config", fixture_id, fixture_sha,
        {"probe": "derived-carrier-partition", "source": "workflow-registry"},
        expected_sha, actual_sha, status,
        digest_of(observed_shape),
        "OK" if status == "PASS" else "CARRIER_PARTITION_MISMATCH",
    )

    # det-17: the render inputs are the blob bytes the fixture pinned.
    expected_sha, actual_sha, status = _match_case(
        fixture.get("render_input_sha256"), render.input_sha256
    )
    rec.add(
        "det-17-render-inputs", None, "config", fixture_id, fixture_sha,
        {"probe": "render-input-blobs", "count": len(render.input_sha256)},
        expected_sha, actual_sha, status,
        digest_of(render.input_sha256),
        "OK" if status == "PASS" else "RENDER_INPUT_MISMATCH",
    )


def run_deterministic(
    repo_root: Path,
    out_dir: Path,
    local_dir: Path,
    fixtures_dir: Path,
    codex_bin: str,
    runner: CodexRunner,
    parent_env: Mapping[str, str],
    user_codex_home: Path,
    stage_parent: Path,
    unit: str = "p1a",
    rev: str | None = None,
) -> tuple[Path, str]:
    started_at = utc_now_rfc3339()
    head_sha = rev or git_head(repo_root)

    fixture_path = fixtures_dir / FIXTURE_NAMES[unit]
    if not fixture_path.is_file():
        _die(f"fixture missing: {fixture_path} (run emit-fixtures --unit {unit} first)")
    fixture_raw = fixture_path.read_bytes()
    fixture_sha = sha256_hex(fixture_raw)
    fixture = _strict_json_loads(fixture_raw, "deterministic fixture")
    fixture_id = fixture["fixture_id"]

    env_user = sanitized_child_env(parent_env, str(user_codex_home))
    build = codex_version(runner, codex_bin, env_user)
    codex_build = build or "unavailable"

    run_id = make_run_id(DET_SCHEMA, started_at, head_sha)
    out_path = out_dir / f"{run_id}.json"
    if out_path.exists():
        _die(f"output already exists (fail closed): {out_path}")
    run_local = local_dir / run_id
    rec = CaseRecorder(run_local, codex_build)

    if build is None:
        rec.add(
            "det-00-codex-available", None, "config", fixture_id, fixture_sha,
            {"probe": "codex --version"}, digest_of(True), digest_of(False),
            "BLOCKED_PREREQUISITE", digest_of(None), "CODEX_UNAVAILABLE",
        )
        return _finish_deterministic(
            rec, out_path, run_id, started_at, head_sha, codex_build
        )

    # -- det-00: fixture pin ---------------------------------------------------
    # Reported as a case rather than a hard exit: a fixture pinned at an older
    # revision is exactly the F6 situation, and the run must SAY so (with the
    # per-capability det-02 mismatches that follow) instead of aborting mute.
    expected_sha, actual_sha, status = _match_case(
        head_sha, fixture.get("pinned_head")
    )
    rec.add(
        "det-00-fixture-pin", None, "config", fixture_id, fixture_sha,
        {"probe": "fixture-pinned-head", "unit": unit},
        expected_sha, actual_sha, status,
        digest_of({"probed_rev": head_sha, "pinned_head": fixture.get("pinned_head")}),
        "OK" if status == "PASS" else "FIXTURE_PIN_STALE",
    )

    # -- det-01: manifest required inventory ---------------------------------
    manifest_ids = load_manifest_required_ids(repo_root)
    expected_sha, actual_sha, status = _match_case(
        fixture["required_ids"], list(manifest_ids)
    )
    rec.add(
        "det-01-manifest-required-inventory", None, "config", fixture_id, fixture_sha,
        {"probe": "manifest-required-set", "path": MANIFEST_PATH},
        expected_sha, actual_sha, status,
        digest_of(list(manifest_ids)),
        "OK" if status == "PASS" else "INVENTORY_MISMATCH",
    )

    # -- det-02/03/05 prerequisites: source blobs ----------------------------
    source_blobs: dict[str, bytes | None] = {}
    for cid in REQUIRED_18:
        try:
            source_blobs[cid] = git_blob_bytes(repo_root, head_sha, f"{SOURCE_ROOT}/{cid}/SKILL.md")
        except GitError:
            source_blobs[cid] = None

    for cid in REQUIRED_18:
        blob = source_blobs[cid]
        expected_source_sha = fixture["source_sha256"].get(cid)
        if blob is None:
            rec.add(
                f"det-02-source-present--{cid}", cid, "skill", fixture_id, fixture_sha,
                {"probe": "git-blob", "rev": "HEAD"},
                expected_source_sha or digest_of(None), digest_of(None),
                "FAIL", digest_of(None), "MISSING_SOURCE",
            )
            continue
        front = parse_frontmatter(blob)
        actual_source_sha = sha256_hex(blob)
        frontmatter_ok = (
            front is not None
            and front.get("name") == cid
            and isinstance(front.get("description"), str)
        )
        if expected_source_sha != actual_source_sha:
            reason = "SOURCE_DIGEST_MISMATCH"
        elif not frontmatter_ok:
            reason = "FRONTMATTER_INVALID"
        else:
            reason = "OK"
        rec.add(
            f"det-02-source-present--{cid}", cid, "skill", fixture_id, fixture_sha,
            {"probe": "git-blob", "rev": "HEAD"},
            expected_source_sha or digest_of(None), actual_source_sha,
            "PASS" if reason == "OK" else "FAIL",
            actual_source_sha,
            reason,
        )

    # -- det-03: derived project path safety ---------------------------------
    for cid in REQUIRED_18:
        problems = path_safety_violations(cid)
        expected_sha, actual_sha, status = _match_case([], problems)
        rec.add(
            f"det-03-derived-path--{cid}", cid, "skill", fixture_id, fixture_sha,
            {"probe": "path-derivation", "root": ARTIFACT_ROOT},
            expected_sha, actual_sha, status,
            digest_of({"path": derived_artifact_path(cid), "problems": problems}),
            "OK" if status == "PASS" else "PATH_UNSAFE",
        )

    # -- det-04: casefold collision over the whole candidate set -------------
    folded: dict[str, list[str]] = {}
    for cid in REQUIRED_18:
        folded.setdefault(derived_artifact_path(cid).casefold(), []).append(cid)
    collisions = sorted(k for k, v in folded.items() if len(v) > 1)
    expected_sha, actual_sha, status = _match_case([], collisions)
    rec.add(
        "det-04-casefold-collision-set", None, "skill", fixture_id, fixture_sha,
        {"probe": "casefold-collision", "set": "required-18"},
        expected_sha, actual_sha, status,
        digest_of(collisions),
        "OK" if status == "PASS" else "CASEFOLD_COLLISION",
    )

    # -- det-06: real-tree byte-copy artifact digests -------------------------
    for cid in BYTE_COPY_5:
        blob = source_blobs[cid]
        try:
            artifact = git_blob_bytes(repo_root, head_sha, f"{ARTIFACT_ROOT}/{cid}/SKILL.md")
        except GitError:
            artifact = None
        expected_sha = sha256_hex(blob) if blob is not None else digest_of(None)
        actual_sha = sha256_hex(artifact) if artifact is not None else digest_of(None)
        status = "PASS" if artifact is not None and blob == artifact else "FAIL"
        rec.add(
            f"det-06-artifact-digest--{cid}", cid, "skill", fixture_id, fixture_sha,
            {"probe": "byte-copy-artifact", "rev": "HEAD"},
            expected_sha, actual_sha, status,
            actual_sha,
            "OK" if status == "PASS" else "ARTIFACT_DIGEST_MISMATCH",
        )

    # -- P1b: production candidate render (plan §5.6) -------------------------
    # The candidates Codex is asked to load below are the EXACT production
    # renderer output for the probed commit, not raw sources.
    description_blobs: dict[str, bytes | None] = dict(source_blobs)
    stage_artifacts: dict[str, bytes] | None = None
    if unit == "p1b":
        try:
            render = build_candidate_render(
                repo_root, head_sha, stage_parent / "render"
            )
        except Exception as exc:  # noqa: BLE001 - any render refusal must be recorded
            # A render that cannot run is a RESULT, not a crash: plan §1.4 requires
            # the condition to enter a structured status and §2.8.6 requires an
            # evidence file to exist. Aborting with a traceback would leave the
            # operator with nothing to read (PR-P1b Stage 11).
            rec.add(
                "det-18-candidate-render", None, "config", fixture_id, fixture_sha,
                {"probe": "production-render", "error": type(exc).__name__},
                digest_of("rendered"), digest_of(None),
                "ERROR", digest_of(f"{type(exc).__name__}: {exc}"[:400]),
                "CANDIDATE_RENDER_FAILED",
            )
            return _finish_deterministic(
                rec, out_path, run_id, started_at, head_sha, codex_build
            )
        stage_artifacts = staged_skill_artifacts(render.outputs)
        description_blobs = {
            path.split("/")[2]: data
            for path, data in render.outputs.items()
            if path.startswith(f"{ARTIFACT_ROOT}/")
        }
        _record_p1b_cases(rec, fixture, fixture_id, fixture_sha, render)

    # -- staged layouts -------------------------------------------------------
    layout = stage_candidate_project(
        repo_root, head_sha, stage_parent,
        artifacts=stage_artifacts, prefix=f"{unit}-stage-",
    )
    canary_server = f"{unit}-canary"
    write_project_codex_config(layout.root, canary_server)
    env_empty = sanitized_child_env(parent_env, str(layout.home_empty))
    env_trusted = sanitized_child_env(parent_env, str(layout.home_trusted))

    # -- det-07: fresh-process discovery matrix ------------------------------
    discovery_runs: list[tuple[str, Path, Mapping[str, str], tuple[str, ...]]] = [
        ("staged-root-isolated", layout.root, env_trusted, REQUIRED_18),
        ("staged-nested-isolated", layout.nested, env_trusted, REQUIRED_18),
        ("staged-worktree-isolated", layout.worktree, env_trusted, REQUIRED_18),
        ("real-root-user-layer", repo_root, env_user, tuple(sorted(BYTE_COPY_5))),
    ]
    staged_prompt_text: str | None = None
    for label, cwd, env, expected_set in discovery_runs:
        result = run_prompt_input(runner, codex_bin, cwd, env)
        evidence_sha = rec.capture(f"prompt-input--{label}.json", result.stdout)
        text = extract_prompt_input_text(result.stdout) if result.returncode == 0 else None
        if text is None:
            rec.add(
                f"det-07-fresh-discovery--{label}", None, "skill", fixture_id, fixture_sha,
                {"probe": "debug prompt-input", "layout": label},
                digest_of(list(expected_set)), digest_of(None),
                "ERROR", evidence_sha, "CAPTURE_UNPARSEABLE",
            )
            continue
        if label == "staged-root-isolated":
            staged_prompt_text = text
        found = tuple(n for n in discovered_skill_names(text) if n in REQUIRED_18)
        expected_sha, actual_sha, status = _match_case(list(expected_set), list(found))
        rec.add(
            f"det-07-fresh-discovery--{label}", None, "skill", fixture_id, fixture_sha,
            {"probe": "debug prompt-input", "layout": label},
            expected_sha, actual_sha, status,
            evidence_sha,
            "OK" if status == "PASS" else "DISCOVERY_SET_MISMATCH",
        )

    # -- det-05: description budget mechanism (staged discovery rendering) ----
    # Owner-ratified criterion: the budget must be deterministic and the rendering
    # legal — either the complete description or an exact prefix truncation at
    # DISCOVERY_BUDGET_CHARS with the "..." marker. Oversize itself is recorded
    # data, not a failure; a malformed or mode-mismatched rendering fails.
    # P1b measures the RENDERED carrier's description (the one Codex will load
    # after cutover), P1a the raw source description; both go through the same
    # scalar-unquoting read.
    predicted_modes: dict[str, Any] = fixture.get("predicted_render_mode", {})
    for cid in REQUIRED_18:
        blob = description_blobs.get(cid)
        description = frontmatter_description(blob) if blob is not None else None
        body = (
            discovery_entry_body(staged_prompt_text, cid)
            if staged_prompt_text is not None
            else None
        )
        if body is None or not isinstance(description, str):
            rec.add(
                f"det-05-description-budget--{cid}", cid, "skill", fixture_id, fixture_sha,
                {"probe": "discovery-budget", "layout": "staged-root-isolated"},
                digest_of(predicted_modes.get(cid)), digest_of(None),
                "BLOCKED_PREREQUISITE", digest_of(None), "CAPTURE_UNPARSEABLE",
            )
            continue
        observed = classify_render_mode(description, body)
        expected_sha, actual_sha, status = _match_case(predicted_modes.get(cid), observed)
        if status == "PASS":
            reason = "OK" if observed == "complete" else "OK_DETERMINISTIC_TRUNCATION"
        elif observed == "malformed":
            reason = "DESCRIPTION_RENDER_MALFORMED"
        else:
            reason = "RENDER_MODE_MISMATCH"
        rec.add(
            f"det-05-description-budget--{cid}", cid, "skill", fixture_id, fixture_sha,
            {"probe": "discovery-budget", "layout": "staged-root-isolated"},
            expected_sha, actual_sha, status,
            digest_of(
                {
                    "description_chars": len(description),
                    "surfaced_chars": len(body),
                    "mode": observed,
                }
            ),
            reason,
        )

    # -- det-08: config / trust route ----------------------------------------
    user_config_path = user_codex_home / "config.toml"
    if user_config_path.is_file():
        entries = parse_user_trust_entries(
            user_config_path.read_text(encoding="utf-8", errors="replace")
        )
        covering = trust_entry_covering(entries, repo_root)
        status = "PASS" if covering else "FAIL"
        rec.add(
            "det-08-trust--user-layer-entry", None, "config", fixture_id, fixture_sha,
            {"probe": "user-config-projects-table"},
            digest_of(True), digest_of(covering is not None), status,
            digest_of({"covering_entry": covering}),
            "OK" if covering else "TRUST_ENTRY_ABSENT",
        )
    else:
        rec.add(
            "det-08-trust--user-layer-entry", None, "config", fixture_id, fixture_sha,
            {"probe": "user-config-projects-table"},
            digest_of(True), digest_of(None),
            "BLOCKED_PREREQUISITE", digest_of(None), "TRUST_ENTRY_ABSENT",
        )

    differential: dict[str, Any] = {}
    for mode, env in (("empty", env_empty), ("trusted", env_trusted)):
        result = run_mcp_list(runner, codex_bin, layout.root, env)
        rec.capture(f"mcp-list--{mode}.json", result.stdout)
        try:
            servers = json.loads(result.stdout.decode("utf-8"))
            differential[mode] = sorted(
                s.get("name") for s in servers if isinstance(s, dict)
            )
        except (json.JSONDecodeError, UnicodeDecodeError):
            differential[mode] = None
    expected_diff = {"empty": [], "trusted": [canary_server]}
    expected_sha, actual_sha, status = _match_case(expected_diff, differential)
    rec.add(
        "det-08-trust--project-config-differential", None, "config", fixture_id, fixture_sha,
        {"probe": "mcp list --json", "layout": "staged-root"},
        expected_sha, actual_sha, status,
        digest_of(differential),
        "OK" if status == "PASS" else "PROJECT_CONFIG_NOT_LOADED",
    )

    project_cfg = repo_root / ".codex" / "config.toml"
    project_names = sorted(
        m.group(1)
        for m in re.finditer(r"^\[mcp_servers\.([A-Za-z0-9_-]+)\]",
                             project_cfg.read_text(encoding="utf-8"), re.M)
    ) if project_cfg.is_file() else []
    if not project_names:
        # An empty expectation would make the subset check pass vacuously —
        # an absent/serverless project config is a missing prerequisite, not PASS.
        rec.add(
            "det-08-trust--real-project-config-loaded", None, "config", fixture_id, fixture_sha,
            {"probe": "mcp list --json", "layout": "real-root-user-layer"},
            digest_of(None), digest_of(None),
            "BLOCKED_PREREQUISITE",
            digest_of({"project_servers": []}),
            "PROJECT_CONFIG_ABSENT",
        )
    else:
        result = run_mcp_list(runner, codex_bin, repo_root, env_user)
        rec.capture("mcp-list--real-user-layer.json", result.stdout)
        try:
            servers = json.loads(result.stdout.decode("utf-8"))
            effective = {s.get("name") for s in servers if isinstance(s, dict)}
            loaded = sorted(n for n in project_names if n in effective)
        except (json.JSONDecodeError, UnicodeDecodeError):
            loaded = None  # type: ignore[assignment]
        expected_sha, actual_sha, status = _match_case(project_names, loaded)
        rec.add(
            "det-08-trust--real-project-config-loaded", None, "config", fixture_id, fixture_sha,
            {"probe": "mcp list --json", "layout": "real-root-user-layer"},
            expected_sha, actual_sha, status,
            digest_of({"project_servers": project_names, "loaded": loaded}),
            "OK" if status == "PASS" else "PROJECT_CONFIG_NOT_LOADED",
        )

    # -- det-09/10: hook / rule canary ----------------------------------------
    features = runner([codex_bin, "features", "list"], repo_root, env_user, 60, None)
    features_text = features.stdout.decode("utf-8", "replace")
    features_sha = rec.capture("features-list.txt", features.stdout)
    hooks_line = re.search(r"^hooks\s+(\S+)\s+(\S+)\s*$", features_text, re.M)
    hooks_state = [hooks_line.group(1), hooks_line.group(2)] if hooks_line else None
    exec_help = runner([codex_bin, "exec", "--help"], repo_root, env_user, 60, None)
    help_text = exec_help.stdout.decode("utf-8", "replace")
    help_sha = rec.capture("exec-help.txt", exec_help.stdout)

    expected_sha, actual_sha, status = _match_case(
        {"feature": ["stable", "true"], "flag": True},
        {"feature": hooks_state, "flag": "--dangerously-bypass-hook-trust" in help_text},
    )
    rec.add(
        "det-09-hook-canary", None, "hook", fixture_id, fixture_sha,
        {"probe": "features list + exec --help"},
        expected_sha, actual_sha, status,
        features_sha,
        "OK" if status == "PASS" else "SURFACE_ABSENT",
    )
    expected_sha, actual_sha, status = _match_case(
        {"flag": True},
        {"flag": "--ignore-rules" in help_text},
    )
    rec.add(
        "det-10-rule-canary", None, "rule", fixture_id, fixture_sha,
        {"probe": "exec --help"},
        expected_sha, actual_sha, status,
        help_sha,
        "OK" if status == "PASS" else "SURFACE_ABSENT",
    )

    return _finish_deterministic(rec, out_path, run_id, started_at, head_sha, codex_build)


def _finish_deterministic(
    rec: CaseRecorder,
    out_path: Path,
    run_id: str,
    started_at: str,
    head_sha: str,
    codex_build: str,
) -> tuple[Path, str]:
    completed_at = utc_now_rfc3339()
    verdict = rec.verdict()
    doc = {
        "schema_version": 1,
        "probe_kind": DET_SCHEMA,
        "run_id": run_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "repo_head": head_sha,
        "codex_build": codex_build,
        "cases": sorted(rec.cases, key=lambda c: c["case_id"]),
        "verdict": verdict,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(canonical_json_bytes(doc))
    return out_path, verdict


# --------------------------------------------------------------------------- #
# telemetry leg
# --------------------------------------------------------------------------- #

WARNING_CODES = (
    "EXEC_NONZERO_EXIT",
    "EXEC_TIMEOUT",
    "EVENT_STREAM_EMPTY",
    "EVENT_STREAM_MALFORMED",
)


def _event_strings(node: Any) -> Iterable[str]:
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _event_strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _event_strings(value)


def _is_agent_prose(event: dict[str, Any]) -> bool:
    item = event.get("item")
    return isinstance(item, dict) and item.get("type") == "agent_message"


def classify_events(stdout: bytes, target_id: str) -> tuple[str, list[str]]:
    """Deterministic trigger classifier over the `codex exec --json` JSONL stream.

    A candidate counts as *invoked* only on a structural signal in a
    non-prose event: a command/tool string referencing its staged carrier path
    (`agents/skills/<id>/SKILL.md`, either slash direction) or a structured
    field equal to the capability id. ``agent_message`` items — the model's own
    prose, including "I will use skill X" self-reports — are skipped entirely:
    a self-report is never trigger evidence (plan §2.8.6 discipline).
    """
    warnings: list[str] = []
    lines = [ln for ln in stdout.decode("utf-8", "replace").splitlines() if ln.strip()]
    if not lines:
        return "UNPARSEABLE", ["EVENT_STREAM_EMPTY"]
    hits: set[str] = set()
    parsed_any = False
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        parsed_any = True
        if _is_agent_prose(event):
            continue
        for value in _event_strings(event):
            # shell commands escape Windows separators, so a path may arrive with
            # any mix of "/", "\" and "\\" — collapse every separator run to "/".
            normalized = re.sub(r"[\\/]+", "/", value)
            for cid in REQUIRED_18:
                if f"agents/skills/{cid}/SKILL.md" in normalized or value == cid:
                    hits.add(cid)
    if not parsed_any:
        return "UNPARSEABLE", ["EVENT_STREAM_MALFORMED"]
    if target_id in hits:
        return "TRIGGERED_TARGET", warnings
    if hits:
        return "TRIGGERED_OTHER", warnings
    return "NOT_TRIGGERED", warnings


def extract_model_id(stdout: bytes) -> str | None:
    for line in stdout.decode("utf-8", "replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        candidates: list[Any] = [event.get("model"), event.get("model_id")]
        msg = event.get("msg")
        if isinstance(msg, dict):
            candidates.extend([msg.get("model"), msg.get("model_id")])
        for value in candidates:
            if isinstance(value, str) and value:
                return value
    return None


def run_telemetry(
    repo_root: Path,
    out_dir: Path,
    local_dir: Path,
    fixtures_dir: Path,
    codex_bin: str,
    runner: CodexRunner,
    parent_env: Mapping[str, str],
    user_codex_home: Path,
    stage_parent: Path,
    limit_capabilities: tuple[str, ...] | None = None,
    model: str | None = None,
    unit: str = "p1a",
    rev: str | None = None,
) -> Path:
    started_at = utc_now_rfc3339()
    head_sha = rev or git_head(repo_root)

    corpus_path = fixtures_dir / CORPUS_NAME
    if not corpus_path.is_file():
        _die(f"corpus fixture missing: {corpus_path}")
    corpus_raw = corpus_path.read_bytes()
    corpus = _strict_json_loads(corpus_raw, "prompt corpus")
    prompts = corpus.get("prompts")
    if not isinstance(prompts, list) or not prompts:
        _die("prompt corpus has no prompts")
    seen_keys: set[tuple[str, str]] = set()
    for entry in prompts:
        if not isinstance(entry, dict) or set(entry) != {
            "capability_id", "prompt_id", "kind", "text",
        }:
            _die("corpus entry keys must be exactly capability_id/prompt_id/kind/text")
        key = (entry["capability_id"], entry["prompt_id"])
        if key in seen_keys:
            _die(f"duplicate corpus entry {key}")
        seen_keys.add(key)
        if not isinstance(entry["text"], str) or not entry["text"].strip():
            _die(f"empty prompt text for {key}")
    try:
        corpus_rel = corpus_path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        _die(f"corpus fixture must live under the repo root: {corpus_path}")
    prompt_fixture_sha = set_digest({corpus_rel: sha256_hex(corpus_raw)})

    env_user = sanitized_child_env(parent_env, str(user_codex_home))
    build = codex_version(runner, codex_bin, env_user)
    if build is None:
        _die("codex binary unavailable; telemetry leg cannot run")

    run_id = make_run_id(TEL_SCHEMA, started_at, head_sha)
    out_path = out_dir / f"{run_id}.json"
    if out_path.exists():
        _die(f"output already exists (fail closed): {out_path}")
    run_local = local_dir / run_id
    run_local.mkdir(parents=True, exist_ok=True)

    # P1b observes implicit triggering against the PRODUCTION-RENDERED carriers:
    # the 13 translated ones carry a compact codex_discovery_summary instead of
    # the long source description P1a measured, so the two runs answer different
    # questions and must stage different bytes.
    stage_artifacts: dict[str, bytes] | None = None
    if unit == "p1b":
        stage_artifacts = staged_skill_artifacts(
            build_candidate_render(
                repo_root, head_sha, stage_parent / "render"
            ).outputs
        )
    layout = stage_candidate_project(
        repo_root, head_sha, stage_parent,
        artifacts=stage_artifacts, prefix=f"{unit}-tel-stage-",
    )
    argv_template = [
        codex_bin, "exec", "--json", "--ephemeral", "--skip-git-repo-check",
        "-s", "read-only", "--ignore-user-config",
    ]
    if model is not None:
        # Explicitly pinning the model makes model_id a recorded fact, not a
        # guessed default; the pin itself is covered by cli_args_sha256.
        argv_template += ["-m", model]
    argv_template.append("-")
    cli_args_sha = digest_of(argv_template[1:])
    # No project-level codex config is in effect for telemetry runs (isolated
    # staging + --ignore-user-config). §2.8.1 closes every *_sha256 field to
    # 64-hex, and §2.8.6 sanctions JSON null only for temperature/seed — so an
    # absent config is recorded as the module's domain-separated absent-value
    # digest (digest of canonical JSON null), never as a raw null.
    project_cfg = layout.root / ".codex" / "config.toml"
    project_config_sha = (
        sha256_hex(project_cfg.read_bytes()) if project_cfg.is_file() else digest_of(None)
    )

    observations: list[dict[str, Any]] = []
    model_id: str | None = model
    all_warnings: set[str] = set()
    for entry in prompts:
        cid = entry["capability_id"]
        if limit_capabilities is not None and cid not in limit_capabilities:
            continue
        prompt_id = entry["prompt_id"]
        prompt_text = entry["text"]
        for run_index in range(1, REPETITIONS + 1):
            # prompt via stdin per the headless-Windows invocation discipline
            result = runner(
                argv_template,
                layout.root,
                env_user,
                EXEC_TIMEOUT_SECONDS,
                prompt_text.encode("utf-8"),
            )
            stdout, rc = result.stdout, result.returncode
            (run_local / f"{prompt_id}--run{run_index}.jsonl").write_bytes(stdout)
            observed_class, warnings = classify_events(stdout, cid)
            if rc == -1:
                warnings.append("EXEC_TIMEOUT")
            elif rc != 0:
                warnings.append("EXEC_NONZERO_EXIT")
            if model_id is None:
                model_id = extract_model_id(stdout)
            all_warnings.update(warnings)
            observations.append(
                {
                    "capability_id": cid,
                    "prompt_id": prompt_id,
                    "run_index": run_index,
                    "observed_class": observed_class,
                    "warning_codes": sorted(set(warnings)),
                }
            )

    observations.sort(key=lambda o: (o["capability_id"], o["prompt_id"], o["run_index"]))
    doc = {
        "schema_version": 1,
        "probe_kind": TEL_SCHEMA,
        "run_id": run_id,
        "started_at": started_at,
        "completed_at": utc_now_rfc3339(),
        "repo_head": head_sha,
        "codex_build": build,
        "model_id": model_id,
        "sampling_config": {
            "reasoning_effort": None,
            "temperature": None,
            "seed": None,
            "cli_args_sha256": cli_args_sha,
            "project_config_sha256": project_config_sha,
        },
        "prompt_fixture_sha256": prompt_fixture_sha,
        "repetitions": REPETITIONS,
        "observations": observations,
        "warnings": sorted(all_warnings),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(canonical_json_bytes(doc))
    return out_path


# --------------------------------------------------------------------------- #
# fixture emission
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# PR-P1b: production candidate render (plan §5.6)
# --------------------------------------------------------------------------- #


class ProductionModules(NamedTuple):
    agents_sync: Any
    skill_renderer: Any
    readme_renderer: Any
    config_renderer: Any
    projection_loader: Any
    check_development_agent: Any
    check_agents_projection: Any


def production_modules() -> ProductionModules:
    """The EXACT production renderer/module/version landed by PR-B (plan §5.6).

    Imported lazily: P1a mode and the offline contract tests must keep working on
    a tree where these modules are absent or irrelevant.
    """
    import scripts.sdd._common.codex_config_renderer as config_mod
    import scripts.sdd._common.codex_readme_renderer as readme_mod
    import scripts.sdd._common.projection_loader as loader_mod
    import scripts.sdd._common.skill_renderer as skill_mod
    import scripts.sdd.agents_sync as sync_mod
    import scripts.sdd.check_agents_projection as projection_mod
    import scripts.sdd.check_development_agent as manifest_mod

    return ProductionModules(
        sync_mod, skill_mod, readme_mod, config_mod, loader_mod, manifest_mod,
        projection_mod,
    )


def render_input_relpaths(mods: ProductionModules) -> tuple[str, ...]:
    """Non-source inputs the v2 desired-state derivation reads from the tree.

    Taken from the production modules' own path constants, never re-typed here,
    so a moved typed source cannot silently drop out of the materialized set.
    """
    return (
        MANIFEST_PATH,
        mods.skill_renderer.WORKFLOW_REGISTRY_RELPATH,
        mods.skill_renderer.TRANSLATION_MAP_RELPATH,
        mods.skill_renderer.PREFACE_RELPATH,
        "sdd/adapters/codex-skills-readme.md",
        ".mcp.json",
    )


def materialize_render_inputs(
    repo_root: Path,
    rev: str,
    dest: Path,
    capability_ids: Iterable[str],
    mods: ProductionModules,
) -> dict[str, str]:
    """Write the render inputs as GIT BLOB bytes into a scratch tree.

    Rendering from blob bytes rather than the checkout is what makes every
    published candidate digest machine-independent: `.gitattributes` `* text=auto`
    gives Windows checkouts CRLF, and the byte-copy output class is
    ``raw-bytes-v1`` (unnormalized), so a worktree render would publish digests
    that Linux CI could never reproduce (plan follow-up F9).
    Returns ``relpath -> blob sha256``.
    """
    shas: dict[str, str] = {}
    relpaths = list(render_input_relpaths(mods)) + [
        f"{SOURCE_ROOT}/{cid}/SKILL.md" for cid in capability_ids
    ]
    for rel in relpaths:
        data = git_blob_bytes(repo_root, rev, rel)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        shas[rel] = sha256_hex(data)
    return shas


def derive_candidate_manifest(
    manifest: dict[str, Any], registry: Any
) -> dict[str, Any]:
    """The candidate v2 manifest PR-C1 will write, DERIVED — never transcribed.

    translated ← the workflow registry's ``capability_id`` set (the registry is the
    §2.5 SoT for which capabilities have a workflow); byte-copy ← the capabilities
    already at ``projection: project``; everything else ``codex_carrier: none``.
    Counts are never hardcoded (AC-04); the derived partition is compared against
    the plan §2.2.1 transcription as a reported CASE, not as an assertion here.
    """
    candidate = json.loads(json.dumps(manifest))  # deep copy, plain data only
    candidate["schema_version"] = 2
    candidate["codex_readme_template_version"] = 1
    workflow_by_capability = {
        w.capability_id: w.workflow_id for w in registry.workflows.values()
    }
    for cap in candidate.get("capabilities") or []:
        if not isinstance(cap, dict):
            continue
        cap_id = str(cap.get("id"))
        cap.pop("carrier_binding", None)
        if cap_id in workflow_by_capability:
            cap["codex_carrier"] = "translated"
            cap["carrier_binding"] = {"workflow_id": workflow_by_capability[cap_id]}
            cap["required"] = True
            cap["projection"] = "project"
        elif cap.get("projection") == "project":
            cap["codex_carrier"] = "byte-copy"
            cap["required"] = True
        else:
            cap["codex_carrier"] = "none"
            continue
        codex = cap.get("codex")
        if not isinstance(codex, dict):
            codex = {}
            cap["codex"] = codex
        codex["support_mode"] = "native"
    return candidate


def candidate_partition(candidate: dict[str, Any]) -> dict[str, list[str]]:
    """Derived carrier partition of a candidate manifest, code-point sorted."""
    out: dict[str, list[str]] = {"byte-copy": [], "translated": []}
    for cap in candidate.get("capabilities") or []:
        if not isinstance(cap, dict):
            continue
        carrier = cap.get("codex_carrier")
        if carrier in out:
            out[carrier].append(str(cap.get("id")))
    return {key: sorted(value) for key, value in out.items()}


def candidate_manifest_violations(
    candidate: dict[str, Any], mods: ProductionModules
) -> list[str]:
    """Manifest-schema violations of the candidate, via the PRODUCTION V8 checks.

    Scope is exactly the checks that decide on the manifest OBJECT alone —
    top-level shape, the v2 carrier schema DA090-096 and the codex posture block.
    Tree-coupled V8 checks (`.agents` entries, canonical counts, evidence paths)
    compare a v2 manifest against a still-v1 artifact tree and would report the
    dormant-vs-cutover gap that PR-C1 closes atomically; they are out of scope
    here and are named as such in the evidence rather than silently skipped.
    """
    mod = mods.check_development_agent
    violations = (
        mod.check_top_level(candidate)
        + mod.check_codex_carrier(candidate)
        + mod.check_codex_posture(candidate)
    )
    return sorted(
        f"{v.code}:{v.capability_id}:{v.message}"
        if hasattr(v, "code")
        else str(v)
        for v in violations
        if getattr(v, "severity", "error") == "error"
    )


def renderer_identity(
    repo_root: Path, rev: str, mods: ProductionModules
) -> dict[str, dict[str, Any]]:
    """Per production module: LF-normalized digest of the imported file, the same
    digest recomputed from the blob at ``rev``, and ``RENDERER_VERSION`` where the
    module declares one.

    Equality of the two digests is what turns "we used the production renderer"
    from a claim into a checkable fact: the module actually executed is byte-equal
    to the module frozen at the probed commit.

    EVERY module in the render pipeline is covered, not just the three renderers
    that declare RENDERER_VERSION. `agents_sync` owns `_v2_desired_state` and the
    byte-copy branch that emits 5 of the 18 carriers verbatim, `projection_loader`
    supplies the digest helpers this very check uses, `check_agents_projection`
    supplies the MCP projection behind the config output, and
    `check_development_agent` is det-11's checker. All of them execute from the
    working tree, and the fixture is emitted from that same tree — so a module
    left uncommitted would otherwise certify its own drift (PR-P1b Stage 11).
    """
    loader = mods.projection_loader
    out: dict[str, dict[str, Any]] = {}
    for module in mods:
        module_file = Path(module.__file__).resolve()
        try:
            relpath = module_file.relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            # Imported from outside the probed repo: report it rather than crash;
            # det-12 will not find it in the fixture and fails closed.
            relpath = module_file.as_posix()
            out[module.__name__] = {
                "relpath": relpath,
                "imported_sha256": loader.module_source_sha256(module_file),
                "blob_sha256": digest_of(None),
                "renderer_version": getattr(module, "RENDERER_VERSION", None),
            }
            continue
        blob = git_blob_bytes(repo_root, rev, relpath)
        out[module.__name__] = {
            "relpath": relpath,
            "imported_sha256": loader.module_source_sha256(module_file),
            "blob_sha256": sha256_hex(blob.replace(b"\r\n", b"\n")),
            "renderer_version": getattr(module, "RENDERER_VERSION", None),
        }
    return out


class CandidateRender(NamedTuple):
    outputs: dict[str, bytes]  # posix relpath -> exact bytes
    entries: dict[str, dict[str, Any]]  # posix relpath -> v2 lock entry
    partition: dict[str, list[str]]
    manifest_violations: list[str]
    renderer_identity: dict[str, dict[str, Any]]
    input_sha256: dict[str, str]
    deterministic: bool
    candidate_manifest_slice_sha256: str


def build_candidate_render(
    repo_root: Path, rev: str, work_dir: Path
) -> CandidateRender:
    """Render the candidate 18 carriers + README + Codex config with the exact
    production modules, twice, from blob-materialized inputs. Writes nothing into
    the repository."""
    mods = production_modules()
    loader = mods.projection_loader
    mat = work_dir / "materialized"
    mat.mkdir(parents=True, exist_ok=True)

    manifest_blob = git_blob_bytes(repo_root, rev, MANIFEST_PATH)
    manifest = yaml.safe_load(manifest_blob.decode("utf-8"))
    registry_blob = git_blob_bytes(
        repo_root, rev, mods.skill_renderer.WORKFLOW_REGISTRY_RELPATH
    )
    registry = mods.skill_renderer.load_workflow_registry(
        registry_blob.decode("utf-8")
    )
    candidate = derive_candidate_manifest(manifest, registry)
    partition = candidate_partition(candidate)
    carrier_ids = partition["byte-copy"] + partition["translated"]

    input_sha = materialize_render_inputs(repo_root, rev, mat, carrier_ids, mods)

    outputs_raw, entries_raw = mods.agents_sync._v2_desired_state(mat, candidate)
    second_raw, _ = mods.agents_sync._v2_desired_state(mat, candidate)
    outputs = {path.as_posix(): data for path, data in outputs_raw.items()}
    second = {path.as_posix(): data for path, data in second_raw.items()}

    return CandidateRender(
        outputs=outputs,
        entries=dict(entries_raw),
        partition=partition,
        manifest_violations=candidate_manifest_violations(candidate, mods),
        renderer_identity=renderer_identity(repo_root, rev, mods),
        input_sha256=input_sha,
        deterministic=outputs == second,
        candidate_manifest_slice_sha256=loader.sha256_of_canonical(
            [
                loader.manifest_capability_slice(cap)
                for cap in candidate.get("capabilities") or []
                if isinstance(cap, dict)
            ]
        ),
    )


def candidate_surface(entry: dict[str, Any]) -> str:
    """Map a v2 lock entry's surface members onto the §2.8.6 `surface` enum."""
    members = entry.get("surface_members") or []
    return "config" if "mcp" in members else "skill"


def staged_skill_artifacts(outputs: Mapping[str, bytes]) -> dict[str, bytes]:
    """The candidate outputs that belong in a staged probe project: the `.agents`
    skills surface only.

    The rendered `.codex/config.toml` is deliberately NOT staged. It declares
    real MCP servers (including database-backed ones), and a probe has no business
    giving a throwaway project a route to spawn them; the deterministic leg already
    pins its exact bytes (det-13) and exercises the trust/config route with a
    purpose-built one-server canary (det-08). Keeping it out also preserves the
    telemetry leg's stated invariant that no project-level codex config is in
    effect, which is what makes `project_config_sha256` honest.
    """
    return {
        path: data for path, data in outputs.items() if path.startswith(".agents/")
    }


def emit_fixtures(
    repo_root: Path, fixtures_dir: Path, head_sha: str | None = None
) -> Path:
    head_sha = head_sha or git_head(repo_root)
    source_shas: dict[str, str] = {}
    description_chars: dict[str, int | None] = {}
    predicted_modes: dict[str, str | None] = {}
    for cid in REQUIRED_18:
        blob = git_blob_bytes(repo_root, head_sha, f"{SOURCE_ROOT}/{cid}/SKILL.md")
        source_shas[cid] = sha256_hex(blob)
        description = frontmatter_description(blob)
        if isinstance(description, str):
            description_chars[cid] = len(description)
            predicted_modes[cid] = predicted_render_mode(description)
        else:
            description_chars[cid] = None
            predicted_modes[cid] = None
    fixture = {
        "fixture_id": f"p1a-deterministic-expected@{head_sha[:12]}",
        "pinned_head": head_sha,
        "required_ids": list(REQUIRED_18),
        "source_sha256": source_shas,
        "source_set_sha256": set_digest(
            {f"{SOURCE_ROOT}/{cid}/SKILL.md": sha for cid, sha in source_shas.items()}
        ),
        "discovery_budget_chars": DISCOVERY_BUDGET_CHARS,
        "description_chars": description_chars,
        "predicted_render_mode": predicted_modes,
    }
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    out = fixtures_dir / FIXTURE_NAME
    out.write_bytes(canonical_json_bytes(fixture))
    return out


def emit_fixtures_p1b(
    repo_root: Path, fixtures_dir: Path, head_sha: str | None = None
) -> Path:
    """Pin the PRODUCTION-RENDERED expectations at ``head_sha`` (plan §5.6).

    Written to its own file: the P1a fixture pins raw-source expectations and
    stays byte-immutable so P1a's published evidence remains recomputable.
    """
    head_sha = head_sha or git_head(repo_root)
    with tempfile.TemporaryDirectory(prefix="p1b-fixture-") as tmp:
        render = build_candidate_render(repo_root, head_sha, Path(tmp))

        source_shas = {
            cid: render.input_sha256[f"{SOURCE_ROOT}/{cid}/SKILL.md"]
            for cid in render.partition["byte-copy"] + render.partition["translated"]
        }
        output_shas = {
            path: sha256_hex(data) for path, data in render.outputs.items()
        }
        description_chars: dict[str, int | None] = {}
        predicted_modes: dict[str, str | None] = {}
        for path, data in render.outputs.items():
            if not path.startswith(f"{ARTIFACT_ROOT}/"):
                continue
            cid = path.split("/")[2]
            description = frontmatter_description(data)
            if isinstance(description, str):
                description_chars[cid] = len(description)
                predicted_modes[cid] = predicted_render_mode(description)
            else:
                description_chars[cid] = None
                predicted_modes[cid] = None

        fixture = {
            "fixture_id": f"p1b-production-render-expected@{head_sha[:12]}",
            "unit": UNIT_LABELS["p1b"],
            "pinned_head": head_sha,
            "required_ids": sorted(source_shas),
            "carrier_partition": render.partition,
            "source_sha256": source_shas,
            "source_set_sha256": set_digest(
                {
                    f"{SOURCE_ROOT}/{cid}/SKILL.md": sha
                    for cid, sha in source_shas.items()
                }
            ),
            "render_input_sha256": render.input_sha256,
            "candidate_output_sha256": output_shas,
            "candidate_set_sha256": set_digest(output_shas),
            "candidate_manifest_slice_sha256": render.candidate_manifest_slice_sha256,
            "renderer_modules": render.renderer_identity,
            "discovery_budget_chars": DISCOVERY_BUDGET_CHARS,
            "description_chars": description_chars,
            "predicted_render_mode": predicted_modes,
        }
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    out = fixtures_dir / P1B_FIXTURE_NAME
    out.write_bytes(canonical_json_bytes(fixture))
    return out


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--local-dir", type=Path, default=None)
    parser.add_argument("--fixtures-dir", type=Path, default=None)
    parser.add_argument("--codex-home", type=Path, default=None,
                        help="user-layer CODEX_HOME (default: ~/.codex)")
    parser.add_argument("--stage-parent", type=Path, default=None,
                        help="parent dir for staged layouts (default: <local-dir>/stage)")
    parser.add_argument("--unit", choices=UNITS, default="p1a",
                        help="delivery unit: p1a = raw source candidates, "
                             "p1b = production renderer output (default: p1a)")
    parser.add_argument("--rev", default=None,
                        help="revision to probe (default: HEAD). P1b pins the "
                             "frozen PR-B merge commit explicitly.")
    parser.add_argument("--limit-capabilities", default=None,
                        help="telemetry only: comma-separated capability subset (pilot runs)")
    parser.add_argument("--model", default=None,
                        help="telemetry only: pin the codex model explicitly (recorded as model_id)")
    parser.add_argument("mode", choices=("emit-fixtures", "deterministic", "telemetry"))
    return parser


def main(argv: list[str] | None = None, runner: CodexRunner = default_codex_runner) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    out_dir = (args.out_dir or repo_root / DEFAULT_OUT_DIR).resolve()
    local_dir = (args.local_dir or repo_root / DEFAULT_LOCAL_DIR).resolve()
    fixtures_dir = (args.fixtures_dir or repo_root / DEFAULT_OUT_DIR / FIXTURES_SUBDIR).resolve()
    codex_home = (args.codex_home or Path.home() / ".codex").resolve()
    stage_parent = (args.stage_parent or local_dir / "stage").resolve()
    rev = resolve_rev(repo_root, args.rev) if args.rev else git_head(repo_root)

    if args.mode == "emit-fixtures":
        emitter = emit_fixtures_p1b if args.unit == "p1b" else emit_fixtures
        out = emitter(repo_root, fixtures_dir, rev)
        print(f"FIXTURES_WRITTEN {out}")
        print(f"FIXTURES_PINNED_HEAD {rev}")
        return 0
    if args.mode == "deterministic":
        out_path, verdict = run_deterministic(
            repo_root, out_dir, local_dir, fixtures_dir, args.codex_bin,
            runner, os.environ, codex_home, stage_parent,
            unit=args.unit, rev=rev,
        )
        print(f"DETERMINISTIC_WRITTEN {out_path}")
        print(f"DETERMINISTIC_VERDICT {verdict}")
        return 0
    limit = tuple(args.limit_capabilities.split(",")) if args.limit_capabilities else None
    out_path = run_telemetry(
        repo_root, out_dir, local_dir, fixtures_dir, args.codex_bin,
        runner, os.environ, codex_home, stage_parent, limit, args.model,
        unit=args.unit, rev=rev,
    )
    print(f"TELEMETRY_WRITTEN {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
