"""Run a declared delivery suite and check its external, version-bound evidence.

This is an integrity gate, not a source attestation or an Owner authorization
credential. Candidate code can still change the harness: independent enforcement
and trusted execution remain separate rollout work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import stat
import subprocess
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "delivery-evidence-v1"
_EXECUTION_SOURCES = {"local": "LOCAL_OFFLINE_RUNTIME",
                      "github-actions": "GITHUB_ACTIONS_UNAUTHENTICATED"}
CLAIMS = {
    "runtime_baseline_eligible": False,
    "owner_accepted": False,
    "independent_source_authenticated": False,
}
_REPO_ROOT = Path(__file__).absolute().parent.parent.parent
_SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
_SAFE_ENV = ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "LANG", "LC_ALL",
             "CI", "GITHUB_ACTIONS", "UV_CACHE_DIR", "UV_PYTHON_INSTALL_DIR")
_MAX_FILE_BYTES = 32 * 1024 * 1024


class EvidenceError(ValueError):
    """A fail-closed evidence integrity error, safe to show without payloads."""

    def __init__(self, message: str, *, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_path(path: Path) -> Path:
    """Reject secret paths and linked ancestors before opening any content."""
    if path.drive and (not re.fullmatch(r"[A-Za-z]:", path.drive) or not path.root):
        raise EvidenceError("UNC/device/drive-relative evidence paths are forbidden")
    absolute = path.absolute()
    for part in absolute.parts:
        if part == absolute.anchor:
            continue
        if (part.endswith((" ", ".")) or any(character in '<>:"|?*\\' or ord(character) < 32
                                              for character in part)
                or re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])",
                                part.split(".", 1)[0].rstrip())):
            raise EvidenceError("noncanonical Windows evidence path component is forbidden")
        lowered = part.lower()
        if (lowered == ".env" or lowered.startswith(".env.")
                or lowered.startswith("secrets") or lowered.endswith((".pem", ".key"))):
            raise EvidenceError("secret path cannot enter delivery evidence")
    for candidate in [absolute, *absolute.parents]:
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise EvidenceError("linked/reparse evidence path is forbidden")
    return absolute.resolve()


def _relative_file(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute() or "\\" in value:
        raise EvidenceError("expected a repository/output-relative file path")
    path = _safe_path(root / value)
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise EvidenceError("evidence file is absent or escapes its declared root")
    if path.stat().st_size > _MAX_FILE_BYTES:
        raise EvidenceError("evidence file exceeds the input size limit")
    return path


def _file_digest(path: Path) -> str:
    safe = _safe_path(path)
    if safe.stat().st_size > _MAX_FILE_BYTES:
        raise EvidenceError("evidence file exceeds the input size limit")
    return _digest(safe.read_bytes())


def _read_json(path: Path) -> dict[str, Any]:
    safe = _safe_path(path)
    if safe.stat().st_size > _MAX_FILE_BYTES:
        raise EvidenceError("JSON input exceeds the input size limit")
    try:
        payload = json.loads(safe.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceError("invalid evidence JSON", exit_code=2) from exc
    if not isinstance(payload, dict):
        raise EvidenceError("evidence JSON must be an object")
    return payload


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def _identifiers(items: list[dict[str, Any]], label: str) -> None:
    values = [item.get("id") for item in items]
    _require(all(isinstance(value, str) and bool(_ID.fullmatch(value)) for value in values),
             f"invalid {label} identifier")
    _require(len(values) == len(set(values)), f"duplicate {label} identifier")


def _paths_digest(root: Path, paths: Any) -> dict[str, str]:
    _require(isinstance(paths, list) and bool(paths), "binding file list must be nonempty")
    _require(all(isinstance(path, str) for path in paths), "invalid binding file list")
    _require(len(paths) == len(set(paths)), "duplicate binding file path")
    return {path: _file_digest(_relative_file(root, path)) for path in paths}


def _load_suite(path: Path, repo_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    safe = _safe_path(path)
    _require(safe.is_relative_to(repo_root.resolve()), "suite must be inside the repository")
    suite = _read_json(safe)
    _require(suite.get("schema_version") == 1, "unsupported delivery suite version")
    commands = suite.get("commands")
    units = suite.get("units")
    _require(isinstance(commands, list) and bool(commands), "commands must be nonempty")
    _require(isinstance(units, list) and bool(units), "units must be nonempty")
    _require(all(isinstance(item, dict) for item in [*commands, *units]), "invalid suite item")
    _identifiers(commands, "command")
    _identifiers(units, "unit")
    command_map = {command["id"]: command for command in commands}
    junit_paths: set[str] = set()
    for command in commands:
        argv = command.get("argv")
        _require(isinstance(argv, list) and bool(argv)
                 and all(isinstance(value, str) and bool(value) for value in argv),
                 "command argv must be a nonempty string list")
        _require(type(command.get("expected_exit")) is int, "command expected_exit must be integer")
        timeout = command.get("timeout_seconds", 300)
        _require(type(timeout) is int and 1 <= timeout <= 3600, "invalid command timeout")
        if "junit" in command:
            junit = command["junit"]
            _require(isinstance(junit, str) and bool(junit) and not Path(junit).is_absolute()
                     and ".." not in Path(junit).parts and "\\" not in junit,
                     "JUnit path must be output-relative")
            _safe_path(Path(junit))
            _require(junit not in junit_paths and junit != "delivery.json"
                     and not junit.endswith(".log"), "JUnit output path collision")
            junit_paths.add(junit)
            _require(type(command.get("min_tests")) is int and command["min_tests"] > 0,
                     "JUnit commands require a positive min_tests")
    unit_bindings = {}
    for unit in units:
        acceptance = unit.get("acceptance")
        _require(isinstance(acceptance, list) and bool(acceptance)
                 and all(isinstance(item, dict) for item in acceptance), "empty acceptance baseline")
        _identifiers(acceptance, "acceptance")
        for ac in acceptance:
            _require(isinstance(ac.get("expected"), str) and bool(ac["expected"].strip()),
                     "acceptance requires an observable expectation")
            _require(ac.get("mode") in {"SELFTEST_SOFTWARE", "BEHAVIOR"}, "invalid evidence mode")
            _require(ac.get("source_kind") in {"synthetic_fixture", "software_test", "actual_observation"},
                     "invalid evidence source kind")
            _require(ac["mode"] == "SELFTEST_SOFTWARE" or ac["source_kind"] == "actual_observation",
                     "synthetic/software tests cannot claim actual behavior acceptance")
            refs = ac.get("command_ids")
            _require(isinstance(refs, list) and bool(refs)
                     and all(isinstance(ref, str) and ref in command_map for ref in refs)
                     and len(set(refs)) == len(refs), "invalid acceptance command references")
            tests = ac.get("tests")
            _require(isinstance(tests, list) and bool(tests), "acceptance needs explicit test identities")
            seen_commands: set[str] = set()
            for binding in tests:
                _require(isinstance(binding, dict), "invalid acceptance test binding")
                ref = binding.get("command_id")
                ids = binding.get("ids")
                _require(isinstance(ref, str) and ref in refs and "junit" in command_map[ref]
                         and ref not in seen_commands, "test binding requires a distinct JUnit command")
                seen_commands.add(ref)
                _require(isinstance(ids, list) and bool(ids)
                         and all(isinstance(value, str) and "::" in value for value in ids)
                         and len(ids) == len(set(ids)), "invalid acceptance test identities")
        unit_bindings[unit["id"]] = {
            "baseline": _paths_digest(repo_root, unit.get("baseline")),
            "inputs": _paths_digest(repo_root, unit.get("inputs")),
        }
    digests = {
        "suite_path": safe.relative_to(repo_root.resolve()).as_posix(),
        "suite_sha256": _file_digest(safe),
        "harness": _paths_digest(repo_root, suite.get("harness")),
        "dependencies": _paths_digest(repo_root, suite.get("dependencies")),
        "units": unit_bindings,
    }
    return suite, digests


def load_suite(path: Path, repo_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        return _load_suite(path, repo_root)
    except EvidenceError as exc:
        raise EvidenceError(str(exc), exit_code=2) from exc


def _git_read(
    repo_root: Path, *argv: str, input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    # Parent GIT_DIR/GIT_WORK_TREE/GIT_INDEX_FILE and replace refs must not redirect
    # the checkout or forge the object graph being bound to this evidence.
    env = {name: value for name in _SAFE_ENV if (value := os.environ.get(name)) is not None}
    path_flags = [] if argv and argv[0] == "check-ignore" else ["--literal-pathspecs"]
    return subprocess.run(["git", "--no-replace-objects", *path_flags, "-C", str(repo_root), *argv],
                          input=input_text, capture_output=True, text=True,
                          check=False, timeout=30, env=env)


def _git_value(repo_root: Path, *argv: str) -> str:
    result = _git_read(repo_root, *argv)
    _require(result.returncode == 0, "cannot determine actual Git objects")
    return result.stdout.strip()


def git_identity(repo_root: Path) -> dict[str, Any]:
    return {
        "tested_sha": _git_value(repo_root, "rev-parse", "HEAD"),
        "tested_tree": _git_value(repo_root, "rev-parse", "HEAD^{tree}"),
        "tracked_worktree_clean": not bool(_git_value(
            repo_root, "status", "--porcelain", "--untracked-files=no")),
    }


def validate_git_relationship(
    repo_root: Path, tested_sha: str, tested_tree: str, head_sha: str, base_sha: str,
) -> None:
    """Bind existing commits to the tested head or exact [base, head] PR merge."""
    for commit in (tested_sha, head_sha, base_sha):
        _require(bool(_SHA.fullmatch(commit)), "invalid actual Git commit identity")
        _require(_git_value(repo_root, "cat-file", "-t", commit) == "commit",
                 "declared head/base/tested object must be an existing local commit")
    _require(_git_value(repo_root, "rev-parse", f"{tested_sha}^{{tree}}") == tested_tree,
             "tested tree does not belong to the tested commit")
    _require(_git_value(repo_root, "rev-parse", "HEAD") == tested_sha,
             "checkout changed while reading its Git identity")
    if tested_sha == head_sha:
        ancestor = _git_read(repo_root, "merge-base", "--is-ancestor", base_sha, head_sha)
        _require(ancestor.returncode == 0, "declared base is not an ancestor of the tested head")
    else:
        ancestry = _git_value(repo_root, "rev-list", "--parents", "-n", "1", tested_sha).split()
        _require(ancestry == [tested_sha, base_sha, head_sha],
                 "tested commit is neither the expected head nor its exact [base, head] PR merge")


def _committed_digest(repo_root: Path, tested_sha: str, relative: str) -> str:
    _require(_git_read(repo_root, "ls-files", "--error-unmatch", "--", relative).returncode == 0,
             "bound repository file is not tracked")
    entry = _git_value(repo_root, "ls-tree", "-z", tested_sha, "--", relative)
    metadata, separator, listed = entry.rstrip("\0").partition("\t")
    fields = metadata.split()
    _require(bool(separator) and listed == relative and len(fields) == 3
             and fields[0] in {"100644", "100755"} and fields[1] == "blob",
             "bound repository file is not a regular blob in the tested tree")
    blob = fields[2]
    _require(int(_git_value(repo_root, "cat-file", "-s", blob)) <= _MAX_FILE_BYTES,
             "committed input exceeds the evidence size limit")
    env = {name: value for name in _SAFE_ENV if (value := os.environ.get(name)) is not None}
    original = subprocess.run(["git", "--no-replace-objects", "-C", str(repo_root),
                               "cat-file", "blob", blob], capture_output=True,
                              check=False, timeout=30, env=env)
    _require(original.returncode == 0, "cannot read the tested tree blob")
    return _digest(original.stdout)


def _reject_untracked_python(repo_root: Path) -> None:
    # Include ignored names: a candidate's .gitignore cannot conceal a new shadow
    # module. Only known ignored dependency/cache directories are exempt.
    unknown = _git_value(repo_root, "ls-files", "--others", "-z").split("\0")
    executable = {".py", ".pyc", ".pyo", ".pyd", ".so", ".dll", ".pth"}
    caches = {".venv", ".cache", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
    allowed = []
    for relative in unknown:
        if not relative or Path(relative).suffix.lower() not in executable:
            continue
        parts = Path(relative).parts
        if parts[0] == ".venv" or (
            Path(relative).suffix.lower() in {".pyc", ".pyo"}
            and (parts[0] in caches or "__pycache__" in parts)
        ):
            allowed.append(relative)
        else:
            raise EvidenceError("untracked Python/executable code can shadow the tested tree")
    if allowed:
        ignored = _git_read(repo_root, "check-ignore", "-z", "--stdin",
                            input_text="\0".join(allowed) + "\0")
        _require(ignored.returncode == 0 and set(allowed) <= set(ignored.stdout.split("\0")),
                 "untracked dependency/cache code is not explicitly ignored")


def validate_checkout_inputs(
    repo_root: Path, tested_sha: str, suite: dict[str, Any], digests: dict[str, Any],
) -> dict[str, str]:
    """Prove bound working bytes and repository command files belong to the tree."""
    paths = {digests["suite_path"]: digests["suite_sha256"],
             **digests["harness"], **digests["dependencies"]}
    for unit in digests["units"].values():
        paths.update(unit["baseline"])
        paths.update(unit["inputs"])
    for command in suite["commands"]:
        previous = ""
        for value in command["argv"]:
            if value.startswith("-") or "{output_dir}" in value or previous in {"-c", "-k", "-m"}:
                previous = value
                continue
            previous = value
            candidate = Path(value)
            absolute = candidate.absolute() if candidate.is_absolute() else (repo_root / candidate).absolute()
            if not absolute.is_relative_to(repo_root.resolve()):
                continue
            safe = _safe_path(absolute)
            if safe.is_file():
                relative = safe.relative_to(repo_root.resolve()).as_posix()
                paths[relative] = _file_digest(safe)
    committed = {}
    for relative, digest in paths.items():
        original = _committed_digest(repo_root, tested_sha, relative)
        _require(original == digest, "bound working content does not match its exact tested tree blob")
        committed[relative] = original
    _reject_untracked_python(repo_root)
    return committed


def junit_integrity(path: Path) -> dict[str, Any]:
    """Recompute counts and identities from actual cases; never trust summary alone."""
    try:
        _file_digest(path)
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError, EvidenceError) as exc:
        raise EvidenceError("missing or malformed JUnit execution output") from exc
    _require(root.tag in {"testsuites", "testsuite"}, "invalid JUnit root")
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    _require(bool(suites), "JUnit output contains no suites")
    cases: dict[str, str] = {}
    for suite in suites:
        direct_cases = suite.findall("testcase")
        counts = {"tests": len(direct_cases), "failures": 0, "errors": 0, "skipped": 0}
        for case in direct_cases:
            classname, name = case.get("classname"), case.get("name")
            _require(bool(classname) and bool(name), "JUnit case is missing its identity")
            identity = f"{classname}::{name}"
            _require(identity not in cases, "duplicate JUnit testcase identity")
            outcomes = [key for key in ("failure", "error", "skipped") if case.find(key) is not None]
            _require(len(outcomes) <= 1, "conflicting JUnit testcase outcomes")
            if outcomes:
                key = {"failure": "failures", "error": "errors", "skipped": "skipped"}[outcomes[0]]
                counts[key] += 1
            cases[identity] = {"failure": "FAIL", "error": "ERROR", "skipped": "SKIP"}.get(
                outcomes[0] if outcomes else "", "PASS")
        for key, actual in counts.items():
            try:
                declared = int(suite.attrib[key])
            except (KeyError, ValueError) as exc:
                raise EvidenceError("JUnit output is missing complete count declarations") from exc
            _require(declared == actual, "JUnit summary does not match its testcase outcomes")
    return {"tests": len(cases), "passed": sum(value == "PASS" for value in cases.values()),
            "failed": sum(value in {"FAIL", "ERROR"} for value in cases.values()),
            "skipped": sum(value == "SKIP" for value in cases.values()), "cases": cases}


def _command_status(command: dict[str, Any], record: dict[str, Any]) -> str:
    if record.get("exit_code") != command["expected_exit"] or record.get("execution_error"):
        return "FAIL"
    if "junit" in command:
        tests = record.get("test_integrity")
        if not isinstance(tests, dict) or tests.get("tests", 0) < command["min_tests"]:
            return "NOT_TESTED"
        if tests["failed"]:
            return "FAIL"
        if tests["skipped"]:
            return "NOT_TESTED"
    return "PASS"


def _acceptance_results(suite: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    commands = {command["id"]: command for command in suite["commands"]}
    observed = {record["id"]: record for record in records}
    units = []
    for unit in suite["units"]:
        results = []
        for ac in unit["acceptance"]:
            actual = []
            statuses = []
            tests_by_command = {binding["command_id"]: binding["ids"] for binding in ac["tests"]}
            for ref in ac["command_ids"]:
                record = observed[ref]
                status = _command_status(commands[ref], record)
                cases = (record.get("test_integrity") or {}).get("cases", {})
                selected = {identity: cases.get(identity, "NOT_TESTED")
                            for identity in tests_by_command.get(ref, [])}
                if any(value != "PASS" for value in selected.values()) and status == "PASS":
                    status = "NOT_TESTED"
                statuses.append(status)
                actual.append({"command_id": ref, "expected_exit": commands[ref]["expected_exit"],
                               "exit_code": record["exit_code"], "status": status, "tests": selected,
                               "output_ref": record["output_ref"]})
            verification = "FAIL" if "FAIL" in statuses else (
                "NOT_TESTED" if "NOT_TESTED" in statuses else "PASS")
            status = "SELFTEST" if verification == "PASS" and ac["mode"] == "SELFTEST_SOFTWARE" else verification
            results.append({**ac, "status": status, "verification_status": verification, "actual": actual})
        units.append({"id": unit["id"], "acceptance": results})
    return units


def _output_root(output_dir: Path, repo_root: Path) -> Path:
    output = _safe_path(output_dir)
    _require(not output.is_relative_to(repo_root.resolve()), "delivery artifacts must remain outside checkout")
    return output


def _binding(args: argparse.Namespace, repo_root: Path) -> dict[str, Any]:
    _require(bool(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository)),
             "invalid repository identity")
    _require(bool(_SHA.fullmatch(args.head_sha)) and bool(_SHA.fullmatch(args.base_sha)),
             "head/base identities must be full Git SHAs")
    kind = getattr(args, "execution_kind", "github-actions")
    if kind == "local":
        valid_url = bool(re.fullmatch(r"local://offline/[A-Za-z0-9][A-Za-z0-9_.-]*", args.run_url))
    elif kind == "github-actions":
        valid_url = bool(re.fullmatch(rf"https://github.com/{re.escape(args.repository)}/actions/runs/[1-9][0-9]*(?:/attempts/[1-9][0-9]*)?", args.run_url))
    else:
        valid_url = False
    if not valid_url:
        raise EvidenceError("execution kind and output source URL do not match", exit_code=2)
    identity = git_identity(repo_root)
    _require(identity.get("tracked_worktree_clean") is True,
             "tested checkout has tracked changes; commit identity cannot bind this candidate")
    validate_git_relationship(repo_root, identity["tested_sha"], identity["tested_tree"],
                              args.head_sha, args.base_sha)
    return {"repository": args.repository, "head_sha": args.head_sha, "base_sha": args.base_sha,
            "run_url": args.run_url, "execution_kind": kind, **identity}


def run_suite(args: argparse.Namespace, repo_root: Path) -> int:
    suite, digests = load_suite(args.suite, repo_root)
    binding = _binding(args, repo_root)
    committed = validate_checkout_inputs(repo_root, binding["tested_sha"], suite, digests)
    output = _output_root(args.output_dir, repo_root)
    output.mkdir(parents=True, exist_ok=False)
    records = []
    safe_env = {name: value for name in _SAFE_ENV if (value := os.environ.get(name)) is not None}
    safe_env.update({"MJ_AGENT_OFFLINE_TEST": "1", "PYTHONNOUSERSITE": "1"})
    for command in suite["commands"]:
        argv = [value.replace("{output_dir}", str(output)) for value in command["argv"]]
        log_name = f"{command['id']}.log"
        record = {"id": command["id"], "argv": command["argv"], "resolved_argv": argv,
                  "expected_exit": command["expected_exit"], "started_at": _now(),
                  "exit_code": None, "execution_error": None, "test_integrity": None,
                  "output_ref": log_name, "run_url": args.run_url}
        try:
            result = subprocess.run(argv, cwd=repo_root, env=safe_env, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, check=False,
                                    timeout=command.get("timeout_seconds", 300))
            log_bytes = result.stdout
            record["exit_code"] = result.returncode
        except (OSError, subprocess.TimeoutExpired) as exc:
            record["execution_error"] = type(exc).__name__
            log_bytes = b"Command could not finish; inspect execution_error.\n"
        log_path = output / log_name
        log_path.write_bytes(log_bytes)
        record.update({"finished_at": _now(), "output_sha256": _file_digest(log_path)})
        if "junit" in command:
            try:
                junit_path = _relative_file(output, command["junit"])
                record["test_integrity"] = junit_integrity(junit_path)
                record["junit_ref"] = command["junit"]
                record["junit_sha256"] = _file_digest(junit_path)
            except EvidenceError as exc:
                if record["execution_error"] is None:
                    record["execution_error"] = str(exc)
        records.append(record)
    # A command may have changed inputs, harness or checkout; never reuse its earlier binding.
    _, after_digests = load_suite(args.suite, repo_root)
    _require(after_digests == digests and _binding(args, repo_root) == binding
             and validate_checkout_inputs(repo_root, binding["tested_sha"], suite, digests) == committed,
             "candidate or evidence inputs changed during execution")
    artifact = {"schema_version": SCHEMA_VERSION, "binding": binding, "digests": digests,
                "committed_files": committed,
                "execution_source": _EXECUTION_SOURCES[binding["execution_kind"]],
                "environment": {"python": platform.python_version(), "platform": platform.platform()},
                "generated_at": _now(), "claims": CLAIMS, "commands": records,
                "units": _acceptance_results(suite, records)}
    (output / "delivery.json").write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n",
                                           encoding="utf-8")
    print(f"delivery_evidence: wrote {output / 'delivery.json'}")
    if any(record["execution_error"] in {"FileNotFoundError", "PermissionError", "OSError"}
           for record in records):
        print("delivery_evidence: FAIL (command could not be launched)")
        return 2
    return check_suite(args, repo_root)


def _timestamp(value: Any) -> datetime:
    _require(isinstance(value, str), "missing execution timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise EvidenceError("invalid execution timestamp") from exc
    _require(parsed.tzinfo is not None, "execution timestamp needs a timezone")
    return parsed


def check_suite(args: argparse.Namespace, repo_root: Path) -> int:
    suite, digests = load_suite(args.suite, repo_root)
    binding = _binding(args, repo_root)
    committed = validate_checkout_inputs(repo_root, binding["tested_sha"], suite, digests)
    output = _output_root(args.output_dir, repo_root)
    artifact = _read_json(_relative_file(output, "delivery.json"))
    if artifact.get("schema_version") != SCHEMA_VERSION:
        raise EvidenceError("unsupported evidence schema", exit_code=2)
    _require(artifact.get("binding") == binding, "evidence does not match expected repository/head/base/tested version")
    _require(artifact.get("execution_source") == _EXECUTION_SOURCES[binding["execution_kind"]],
             "execution source cannot be relabelled as another local or cloud runtime")
    _require(artifact.get("digests") == digests, "acceptance/input/dependency/harness versions do not match")
    _require(artifact.get("committed_files") == committed, "repository bindings do not belong to the tested tree")
    _require(artifact.get("claims") == CLAIMS, "evidence cannot declare authorization or runtime baseline eligibility")
    environment = artifact.get("environment")
    _require(isinstance(environment, dict) and all(isinstance(environment.get(key), str)
             and environment[key] for key in ("python", "platform")), "missing execution environment")
    generated = _timestamp(artifact.get("generated_at"))
    records = artifact.get("commands")
    _require(isinstance(records, list) and len(records) == len(suite["commands"]),
             "missing command execution evidence")
    for command, record in zip(suite["commands"], records, strict=True):
        _require(isinstance(record, dict), "invalid command execution record")
        _require(record.get("id") == command["id"] and record.get("argv") == command["argv"]
                 and record.get("expected_exit") == command["expected_exit"], "command identity mismatch")
        _require(record.get("resolved_argv") == [value.replace("{output_dir}", str(output))
                 for value in command["argv"]], "executed command does not match the suite")
        _require(record.get("run_url") == args.run_url, "command output run link mismatch")
        _require(type(record.get("exit_code")) is int or record.get("execution_error") is not None,
                 "command execution has no exit result")
        _require(_timestamp(record.get("started_at")) <= _timestamp(record.get("finished_at")) <= generated,
                 "command execution timestamps are inconsistent")
        _require(record.get("output_ref") == f"{command['id']}.log", "command log identity mismatch")
        log = _relative_file(output, record["output_ref"])
        _require(record.get("output_sha256") == _file_digest(log), "missing or modified original command output")
        if "junit" in command:
            _require(record.get("junit_ref") == command["junit"], "JUnit output identity mismatch")
            junit = _relative_file(output, record["junit_ref"])
            _require(record.get("junit_sha256") == _file_digest(junit), "JUnit output digest mismatch")
            _require(record.get("test_integrity") == junit_integrity(junit),
                     "test execution completeness/result declarations do not match actual cases")
        else:
            _require(record.get("test_integrity") is None, "non-test command cannot claim test execution")
    expected_units = _acceptance_results(suite, records)
    _require(artifact.get("units") == expected_units, "AC expected/actual results or statuses are inconsistent")
    _require(all(_command_status(command, record) == "PASS"
                 for command, record in zip(suite["commands"], records, strict=True)),
             "command failed or tests were incomplete/skipped")
    _require(all(ac["verification_status"] == "PASS" for unit in expected_units for ac in unit["acceptance"]),
             "acceptance has unverified, failed or missing test outcomes")
    print("delivery_evidence: integrity OK; candidate source is not independently authenticated")
    return 0


def main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "check"))
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--execution-kind", choices=("local", "github-actions"),
                        default="github-actions")
    parser.add_argument("--run-url", required=True)
    args = parser.parse_args(argv)
    root = (repo_root or _REPO_ROOT).resolve()
    if not args.suite.is_absolute():
        args.suite = root / args.suite
    try:
        return run_suite(args, root) if args.action == "run" else check_suite(args, root)
    except (EvidenceError, OSError, KeyError, TypeError, ValueError, subprocess.TimeoutExpired) as exc:
        # No input content, environment values or raw subprocess errors are printed.
        print(f"delivery_evidence: FAIL ({exc if isinstance(exc, EvidenceError) else type(exc).__name__})")
        return exc.exit_code if isinstance(exc, EvidenceError) else 2


if __name__ == "__main__":
    raise SystemExit(main())
