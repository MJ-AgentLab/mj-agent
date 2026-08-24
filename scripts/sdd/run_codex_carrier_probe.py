"""scripts/sdd/run_codex_carrier_probe.py — Epic #499 PR-P1a runtime feasibility probe.

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

Design points the plan leaves to the producer (Owner-ratified at PR-P1a Gate 1):

- ``observed_class`` closed enum: ``TRIGGERED_TARGET | TRIGGERED_OTHER |
  NOT_TRIGGERED | UNPARSEABLE``. Classification parses the ``codex exec --json``
  event stream deterministically; it never uses the model's self-report.
- description budget: a candidate PASSes when its full source frontmatter
  description survives, uncut, into the fresh-process discovery rendering
  (``codex debug prompt-input``) of the staged 18-candidate layout.
- raw captures (prompt-input JSON, mcp list output, exec event streams) stay in
  the gitignored local dir; the tracked evidence files carry digests only, so
  user-layer configuration details never enter the repository.

Candidate bytes are taken from the **git blob** (``git show HEAD:<path>``), never
the worktree file: `.gitattributes` makes Windows checkouts CRLF while the blob
is LF, and a worktree-byte identity could not be reproduced on Linux CI.

Canonicalization follows plan §2.8.1 (canonical JSON, RFC 3339 UTC seconds,
run ID ``<schema>-<YYYYMMDDTHHMMSSZ>-<head12>``, fail-closed on an existing
output path) and §2.7 (set digest = SHA-256 over the canonical JSON object
``path -> raw_sha256`` with code-point-sorted keys).

Subcommands:

``emit-fixtures``   pin the current tree's expected values into the tracked
                    fixture file (authoring step; committed with the probe).
``deterministic``   run the deterministic gate; write one evidence JSON.
``telemetry``       run the model-telemetry leg; write one evidence JSON.

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

EPIC_ID = 499
UNIT_ID = "PR-P1a"

DET_SCHEMA = "deterministic-gate-v1"
TEL_SCHEMA = "model-telemetry-v1"

DEFAULT_OUT_DIR = Path("evidence/development-agent-v8/probe")
DEFAULT_LOCAL_DIR = Path(".mj-agent-local/probe")
FIXTURE_NAME = "deterministic-expected.json"
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
) -> StagedLayout:
    """Materialize the 18 candidate artifacts (raw git-blob bytes) into a fresh git
    project with nested dir + linked worktree, plus two isolated CODEX_HOME dirs.
    """
    stage_parent.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="p1a-stage-", dir=str(stage_parent)))
    candidate_shas: dict[str, str] = {}
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
    (root / "AGENTS.md").write_bytes(
        b"# staged candidate project (PR-P1a probe fixture)\n\n"
        b"Synthetic layout; carries the 18 required candidate carriers only.\n"
    )
    nested = root / "nested" / "inner"
    nested.mkdir(parents=True)
    (nested / "README.md").write_bytes(b"nested cwd marker\n")

    _run_git_in(root, "init", "-q")
    _run_git_in(root, "config", "user.email", "probe@localhost")
    _run_git_in(root, "config", "user.name", "p1a-probe")
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
) -> tuple[Path, str]:
    started_at = utc_now_rfc3339()
    head_sha = git_head(repo_root)

    fixture_path = fixtures_dir / FIXTURE_NAME
    if not fixture_path.is_file():
        _die(f"fixture missing: {fixture_path} (run emit-fixtures first)")
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

    # -- staged layouts -------------------------------------------------------
    layout = stage_candidate_project(repo_root, head_sha, stage_parent)
    canary_server = "p1a-canary"
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
    predicted_modes: dict[str, Any] = fixture.get("predicted_render_mode", {})
    for cid in REQUIRED_18:
        blob = source_blobs[cid]
        front = parse_frontmatter(blob) if blob is not None else None
        description = front.get("description") if front else None
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
) -> Path:
    started_at = utc_now_rfc3339()
    head_sha = git_head(repo_root)

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

    layout = stage_candidate_project(repo_root, head_sha, stage_parent)
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


def emit_fixtures(repo_root: Path, fixtures_dir: Path) -> Path:
    head_sha = git_head(repo_root)
    source_shas: dict[str, str] = {}
    description_chars: dict[str, int | None] = {}
    predicted_modes: dict[str, str | None] = {}
    for cid in REQUIRED_18:
        blob = git_blob_bytes(repo_root, head_sha, f"{SOURCE_ROOT}/{cid}/SKILL.md")
        source_shas[cid] = sha256_hex(blob)
        front = parse_frontmatter(blob)
        description = front.get("description") if front else None
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

    if args.mode == "emit-fixtures":
        out = emit_fixtures(repo_root, fixtures_dir)
        print(f"FIXTURES_WRITTEN {out}")
        return 0
    if args.mode == "deterministic":
        out_path, verdict = run_deterministic(
            repo_root, out_dir, local_dir, fixtures_dir, args.codex_bin,
            runner, os.environ, codex_home, stage_parent,
        )
        print(f"DETERMINISTIC_WRITTEN {out_path}")
        print(f"DETERMINISTIC_VERDICT {verdict}")
        return 0
    limit = tuple(args.limit_capabilities.split(",")) if args.limit_capabilities else None
    out_path = run_telemetry(
        repo_root, out_dir, local_dir, fixtures_dir, args.codex_bin,
        runner, os.environ, codex_home, stage_parent, limit, args.model,
    )
    print(f"TELEMETRY_WRITTEN {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
