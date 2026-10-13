"""Verify original delivery ZIP bytes against explicit expectations and existing Git objects.

This reads evidence without running its commands or authenticating its execution source.
The original collector's run/check contract and three false claims remain unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform
import re
import stat
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Never, cast

if __package__:
    from scripts.sdd import delivery_evidence as evidence
else:
    import delivery_evidence as evidence  # type: ignore[no-redef]

MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_MEMBER_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_MEMBERS = 512
GIT_TIMEOUT_SECONDS = 30
_REPO_ROOT = Path(__file__).absolute().parent.parent.parent
_SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
_XML_DECLARATION = re.compile(
    rb"<\x00*!\x00*(?:D\x00*O\x00*C\x00*T\x00*Y\x00*P\x00*E|E\x00*N\x00*T\x00*I\x00*T\x00*Y)",
    re.IGNORECASE,
)
_SOURCES = {"local": "LOCAL_OFFLINE_RUNTIME", "github-actions": "GITHUB_ACTIONS_UNAUTHENTICATED"}
_CLAIMS = {"runtime_baseline_eligible": False, "owner_accepted": False,
           "independent_source_authenticated": False}
_SAFE_ENV = ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "LANG", "LC_ALL")


class ArchiveError(ValueError):
    """Only controlled, non-payload error codes cross the CLI boundary."""

    def __init__(self, code: str, exit_code: int = 1) -> None:
        super().__init__(code)
        self.exit_code = exit_code


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ArchiveError(code)


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _equal(left: Any, right: Any) -> bool:
    # JSON comparison preserves bool/int distinctions that Python equality loses.
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(
        right, sort_keys=True, allow_nan=False)


def _component(value: str) -> None:
    _require(bool(value) and value not in {".", ".."} and not value.endswith((" ", "."))
             and not any(c in '<>:"|?*\\/' or ord(c) < 32 for c in value)
             and not re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])",
                                  value.split(".", 1)[0]), "UNSAFE_PATH")
    lower = value.lower()
    _require(lower != ".env" and not lower.startswith((".env.", "secrets"))
             and not lower.endswith((".pem", ".key")), "SECRET_PATH")


def _relative(value: Any) -> str:
    _require(isinstance(value, str) and bool(value) and not value.startswith("/"),
             "UNSAFE_RELATIVE_PATH")
    for part in value.split("/"):
        _component(part)
    _require(PurePosixPath(value).as_posix() == value, "AMBIGUOUS_PATH")
    return cast(str, value)


def _host_path(value: Path) -> Path:
    try:
        return evidence._safe_path(value)
    except evidence.EvidenceError as exc:
        raise ArchiveError("UNSAFE_HOST_PATH", 2) from exc


def _object(data: bytes) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            _require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result

    def constant(_: str) -> None:
        raise ArchiveError("NONFINITE_JSON")

    try:
        result = json.loads(data, object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ArchiveError("INVALID_JSON") from exc
    _require(isinstance(result, dict), "JSON_OBJECT_REQUIRED")
    return cast(dict[str, Any], result)


class GitObjects:
    """Read only literal, existing objects; no replace refs, redirects or writes."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.env = {key: value for key in _SAFE_ENV
                    if (value := os.environ.get(key)) is not None}
        self.env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_SYSTEM": os.devnull,
                         "GIT_CONFIG_GLOBAL": os.devnull, "GIT_NO_LAZY_FETCH": "1",
                         "GIT_TERMINAL_PROMPT": "0"})
        self.cache: dict[str, bytes] = {}

    def read(self, *argv: str, false_code: str | None = None) -> bytes:
        try:
            result = subprocess.run(
                ["git", "--no-replace-objects", "--no-lazy-fetch", "--no-optional-locks", "--literal-pathspecs",
                 "-C", str(self.root), *argv], env=self.env, capture_output=True,
                check=False, timeout=GIT_TIMEOUT_SECONDS)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ArchiveError("UNMET_DEPENDENCY_GIT", 2) from exc
        if result.returncode:
            if result.returncode == 1 and false_code is not None:
                raise ArchiveError(false_code)
            raise ArchiveError("UNMET_DEPENDENCY_GIT_OBJECT", 2)
        return result.stdout

    def text(self, *argv: str) -> str:
        return self.read(*argv).decode("utf-8").strip()

    def blob(self, commit: str, relative: str, *, optional: bool = False) -> bytes | None:
        name = _relative(relative)
        if name in self.cache:
            return self.cache[name]
        entry = self.read("ls-tree", "-z", commit, "--", name)
        if not entry and optional:
            return None
        if not entry:
            raise ArchiveError("UNMET_DEPENDENCY_GIT_BLOB", 2)
        metadata, separator, listed = entry.rstrip(b"\0").partition(b"\t")
        fields = metadata.split()
        if optional and fields and fields[1] == b"tree":
            return None
        _require(bool(separator) and listed == name.encode() and len(fields) == 3
                 and fields[0] in {b"100644", b"100755"} and fields[1] == b"blob",
                 "BOUND_FILE_NOT_REGULAR_BLOB")
        oid = fields[2].decode("ascii")
        size = int(self.text("cat-file", "-s", oid))
        _require(0 <= size <= MAX_MEMBER_BYTES, "GIT_BLOB_LIMIT")
        data = self.read("cat-file", "blob", oid)
        _require(len(data) == size, "GIT_BLOB_SIZE_MISMATCH")
        self.cache[name] = data
        return data

    def relationship(self, args: argparse.Namespace) -> None:
        for oid in (args.head_sha, args.base_sha, args.tested_sha):
            _require(self.text("cat-file", "-t", oid) == "commit", "EXPECTED_COMMIT_OBJECT")
        _require(self.text("rev-parse", f"{args.tested_sha}^{{tree}}") == args.tested_tree,
                 "TESTED_TREE_MISMATCH")
        if args.tested_sha == args.head_sha:
            self.read("merge-base", "--is-ancestor", args.base_sha, args.head_sha,
                      false_code="BASE_NOT_ANCESTOR")
        else:
            _require(self.text("rev-list", "--parents", "-n", "1", args.tested_sha).split()
                     == [args.tested_sha, args.base_sha, args.head_sha], "MERGE_PARENT_ORDER")


def _paths(git: GitObjects, commit: str, paths: Any) -> dict[str, str]:
    _require(isinstance(paths, list) and bool(paths)
             and all(isinstance(p, str) for p in paths) and len(paths) == len(set(paths)),
             "INVALID_BINDING_PATHS")
    return {path: _digest(git.blob(commit, path) or b"") for path in paths}


def _identities(items: Any) -> list[dict[str, Any]]:
    _require(isinstance(items, list) and bool(items)
             and all(isinstance(item, dict) for item in items), "INVALID_SUITE_ITEMS")
    ids = [item.get("id") for item in items]
    _require(all(isinstance(i, str) and _ID.fullmatch(i) for i in ids)
             and len(ids) == len(set(ids)), "INVALID_SUITE_IDENTITIES")
    return cast(list[dict[str, Any]], items)


def _suite(git: GitObjects, args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    raw = git.blob(args.tested_sha, args.suite)
    _require(raw is not None, "MISSING_SUITE")
    suite = _object(raw or b"")
    _require(type(suite.get("schema_version")) is int and suite["schema_version"] == 1,
             "SUITE_SCHEMA")
    commands = _identities(suite.get("commands"))
    units = _identities(suite.get("units"))
    command_map = {c["id"]: c for c in commands}
    outputs = {"delivery.json"}
    for command in commands:
        argv = command.get("argv")
        _require(isinstance(argv, list) and bool(argv)
                 and all(isinstance(v, str) and bool(v) for v in argv), "SUITE_ARGV")
        _require(type(command.get("expected_exit")) is int, "SUITE_EXPECTED_EXIT")
        timeout = command.get("timeout_seconds", 300)
        _require(type(timeout) is int and 1 <= timeout <= 3600, "SUITE_TIMEOUT")
        outputs.add(command["id"] + ".log")
    for command in commands:
        if "junit" in command:
            path = _relative(command["junit"])
            _require(path not in outputs and not path.endswith(".log"), "SUITE_OUTPUT_COLLISION")
            outputs.add(path)
            _require(type(command.get("min_tests")) is int and command["min_tests"] > 0,
                     "SUITE_MIN_TESTS")
    unit_bindings = {}
    for unit in units:
        _identities(unit.get("acceptance"))
        for ac in unit["acceptance"]:
            _require(isinstance(ac.get("expected"), str) and bool(ac["expected"].strip()), "AC_EXPECTATION")
            _require(ac.get("mode") in {"SELFTEST_SOFTWARE", "BEHAVIOR"}
                     and ac.get("source_kind") in {"synthetic_fixture", "software_test", "actual_observation"}
                     and (ac["mode"] == "SELFTEST_SOFTWARE" or ac["source_kind"] == "actual_observation"),
                     "AC_SOURCE_MODE")
            refs = ac.get("command_ids")
            _require(isinstance(refs, list) and bool(refs)
                     and all(isinstance(r, str) and r in command_map for r in refs)
                     and len(refs) == len(set(refs)), "AC_COMMAND_REFS")
            bindings = ac.get("tests")
            _require(isinstance(bindings, list) and bool(bindings), "AC_TEST_BINDINGS")
            seen = set()
            for item in bindings:
                _require(isinstance(item, dict), "AC_TEST_BINDINGS")
                ref, ids = item.get("command_id"), item.get("ids")
                _require(isinstance(ref, str) and ref in refs and ref not in seen
                         and "junit" in command_map[ref], "AC_TEST_COMMAND")
                seen.add(ref)
                _require(isinstance(ids, list) and bool(ids)
                         and all(isinstance(i, str) and "::" in i for i in ids)
                         and len(ids) == len(set(ids)), "AC_TEST_IDENTITIES")
        unit_bindings[unit["id"]] = {
            "baseline": _paths(git, args.tested_sha, unit.get("baseline")),
            "inputs": _paths(git, args.tested_sha, unit.get("inputs")),
        }
    digests = {"suite_path": args.suite, "suite_sha256": _digest(raw or b""),
               "harness": _paths(git, args.tested_sha, suite.get("harness")),
               "dependencies": _paths(git, args.tested_sha, suite.get("dependencies")),
               "units": unit_bindings}
    committed = {args.suite: digests["suite_sha256"], **digests["harness"], **digests["dependencies"]}
    for binding in unit_bindings.values():
        committed.update(binding["baseline"])
        committed.update(binding["inputs"])
    for command in commands:
        previous = ""
        for value in command["argv"]:
            excluded = value.startswith("-") or "{output_dir}" in value or previous in {"-c", "-k", "-m"}
            previous = value
            # The original collector accepts '.' as a directory argument (for
            # example --root .). It binds files only; a directory is not a blob.
            if excluded or value == "." or PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute():
                continue
            data = git.blob(args.tested_sha, value, optional=True)
            if data is not None:
                committed[value] = _digest(data)
    return suite, digests, committed


def _archive(data: bytes) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            _require(0 < len(entries) <= MAX_MEMBERS, "ZIP_MEMBER_LIMIT")
            names: set[str] = set()
            folded: set[str] = set()
            total = 0
            for entry in entries:
                name = _relative(entry.filename)
                _require(name not in names and name.casefold() not in folded, "DUPLICATE_ZIP_MEMBER")
                _require(not entry.is_dir() and not entry.flag_bits & 1
                         and entry.compress_type in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED},
                         "UNSUPPORTED_ZIP_MEMBER")
                mode = entry.external_attr >> 16
                _require(stat.S_IFMT(mode) in {0, stat.S_IFREG} and not entry.external_attr & 0x18,
                         "ZIP_MEMBER_NOT_REGULAR")
                _require(0 <= entry.file_size <= MAX_MEMBER_BYTES, "ZIP_MEMBER_SIZE_LIMIT")
                total += entry.file_size
                _require(total <= MAX_TOTAL_BYTES, "ZIP_TOTAL_SIZE_LIMIT")
                names.add(name)
                folded.add(name.casefold())
            for name in names:
                _require(not any(p.as_posix() in names for p in PurePosixPath(name).parents
                                 if p.as_posix() != "."), "ZIP_PATH_COLLISION")
            result = {}
            for entry in entries:
                with archive.open(entry) as handle:
                    content = handle.read(MAX_MEMBER_BYTES + 1)
                _require(len(content) == entry.file_size and len(content) <= MAX_MEMBER_BYTES,
                         "ZIP_MEMBER_SIZE_MISMATCH")
                result[entry.filename] = content
            return result
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
        raise ArchiveError("INVALID_ZIP") from exc


def _original_root(value: str) -> None:
    if value.startswith("/") and not value.startswith("//"):
        path: PurePosixPath | PureWindowsPath = PurePosixPath(value)
        _require(path.as_posix() == value, "AMBIGUOUS_OUTPUT_ROOT")
    else:
        path = PureWindowsPath(value)
        _require(bool(re.fullmatch(r"[A-Za-z]:", path.drive)) and path.is_absolute(),
                 "INVALID_OUTPUT_ROOT")
        _require(value in {str(path), path.as_posix()}, "AMBIGUOUS_OUTPUT_ROOT")
    for part in path.parts[1:]:
        _component(part)


def _resolved_root(template: list[str], observed: Any, previous_root: str | None) -> str | None:
    _require(isinstance(observed, list) and len(template) == len(observed)
             and all(isinstance(v, str) for v in observed), "RESOLVED_ARGV_SHAPE")
    root = previous_root
    for declared, executed in zip(template, observed, strict=True):
        if "{output_dir}" not in declared:
            _require(declared == executed, "RESOLVED_ARGV_CHANGED")
            continue
        if root is None:
            parts = declared.split("{output_dir}")
            pattern = re.escape(parts[0]) + "(?P<root>.+?)" + re.escape(parts[1])
            for part in parts[2:]:
                pattern += "(?P=root)" + re.escape(part)
            match = re.fullmatch(pattern, executed)
            _require(match is not None, "OUTPUT_ROOT_EXPANSION")
            root = match.group("root") if match else ""
            _original_root(root)
        _require(executed == declared.replace("{output_dir}", root), "MIXED_OUTPUT_ROOTS")
    return root


def _junit(data: bytes) -> dict[str, Any]:
    # Scan declarations in ASCII-compatible and UTF-16/32 encodings without
    # rewriting the original XML bytes or resolving any entity declarations.
    _require(_XML_DECLARATION.search(data) is None, "UNSAFE_XML")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ArchiveError("INVALID_JUNIT") from exc
    _require(root.tag in {"testsuite", "testsuites"}, "INVALID_JUNIT_ROOT")
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    _require(bool(suites), "MISSING_JUNIT_SUITE")
    cases: dict[str, str] = {}
    for suite in suites:
        actual = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
        for case in suite.findall("testcase"):
            name, classname = case.get("name"), case.get("classname")
            _require(bool(name) and bool(classname), "MISSING_CASE_IDENTITY")
            identity = f"{classname}::{name}"
            _require(identity not in cases, "DUPLICATE_CASE_IDENTITY")
            outcomes = [key for key in ("failure", "error", "skipped") if case.find(key) is not None]
            _require(len(outcomes) <= 1, "CONFLICTING_CASE_OUTCOMES")
            outcome = outcomes[0] if outcomes else ""
            cases[identity] = {"failure": "FAIL", "error": "ERROR", "skipped": "SKIP"}.get(outcome, "PASS")
            actual["tests"] += 1
            if outcome:
                actual[{"failure": "failures", "error": "errors", "skipped": "skipped"}[outcome]] += 1
        try:
            declared = {key: int(suite.attrib[key]) for key in actual}
        except (KeyError, ValueError) as exc:
            raise ArchiveError("INVALID_JUNIT_COUNTS") from exc
        _require(declared == actual, "JUNIT_COUNT_MISMATCH")
    _require(len(cases) == len(list(root.iter("testcase"))), "UNACCOUNTED_JUNIT_CASE")
    return {"tests": len(cases), "passed": sum(v == "PASS" for v in cases.values()),
            "failed": sum(v in {"FAIL", "ERROR"} for v in cases.values()),
            "skipped": sum(v == "SKIP" for v in cases.values()), "cases": cases}


def _verify(args: argparse.Namespace, root: Path) -> dict[str, Any]:
    archive = _host_path(args.archive)
    if not archive.is_file():
        raise ArchiveError("ARCHIVE_NOT_FILE", 2)
    _require(archive.stat().st_size <= MAX_ARCHIVE_BYTES, "ARCHIVE_SIZE_LIMIT")
    with archive.open("rb") as handle:
        data = handle.read(MAX_ARCHIVE_BYTES + 1)
    _require(len(data) <= MAX_ARCHIVE_BYTES and _digest(data) == args.archive_sha256,
             "ARCHIVE_DIGEST_MISMATCH")
    git = GitObjects(root)
    git.relationship(args)
    suite, digests, committed = _suite(git, args)
    members = _archive(data)
    expected_members = {"delivery.json", *(c["id"] + ".log" for c in suite["commands"]),
                        *(c["junit"] for c in suite["commands"] if "junit" in c)}
    _require(set(members) == expected_members, "ARCHIVE_MEMBER_SET")
    artifact = _object(members["delivery.json"])
    _require(artifact.get("schema_version") == evidence.SCHEMA_VERSION, "EVIDENCE_SCHEMA")
    binding = {"repository": args.repository, "head_sha": args.head_sha, "base_sha": args.base_sha,
               "tested_sha": args.tested_sha, "tested_tree": args.tested_tree,
               "execution_kind": args.execution_kind, "run_url": args.run_url,
               "tracked_worktree_clean": True}
    _require(_equal(artifact.get("binding"), binding), "EXECUTION_BINDING_MISMATCH")
    _require(artifact.get("execution_source") == _SOURCES[args.execution_kind], "SOURCE_RELABELLED")
    _require(_equal(artifact.get("digests"), digests), "BOUND_DIGESTS_MISMATCH")
    _require(_equal(artifact.get("committed_files"), committed), "COMMITTED_BLOBS_MISMATCH")
    _require(_equal(artifact.get("claims"), _CLAIMS), "FALSE_CLAIMS_REQUIRED")
    environment = artifact.get("environment")
    _require(isinstance(environment, dict) and all(isinstance(environment.get(k), str)
             and bool(environment[k]) for k in ("python", "platform")), "EXECUTION_ENVIRONMENT")
    generated = evidence._timestamp(artifact.get("generated_at"))
    records = artifact.get("commands")
    _require(isinstance(records, list) and len(records) == len(suite["commands"]), "COMMAND_COMPLETENESS")
    records = cast(list[dict[str, Any]], records)
    output_root = None
    prior_finish = None
    for command, record in zip(suite["commands"], records, strict=True):
        _require(isinstance(record, dict) and record.get("id") == command["id"]
                 and _equal(record.get("argv"), command["argv"])
                 and _equal(record.get("expected_exit"), command["expected_exit"]), "COMMAND_IDENTITY")
        output_root = _resolved_root(command["argv"], record.get("resolved_argv"), output_root)
        _require(record.get("run_url") == args.run_url and type(record.get("exit_code")) is int
                 and record.get("execution_error") is None, "COMMAND_EXECUTION_RESULT")
        started, finished = evidence._timestamp(record.get("started_at")), evidence._timestamp(record.get("finished_at"))
        _require(started <= finished <= generated and (prior_finish is None or prior_finish <= started),
                 "EXECUTION_TIME_ORDER")
        prior_finish = finished
        log = command["id"] + ".log"
        _require(record.get("output_ref") == log and record.get("output_sha256") == _digest(members[log]),
                 "ORIGINAL_LOG_MISMATCH")
        if "junit" in command:
            junit = command["junit"]
            _require(record.get("junit_ref") == junit
                     and record.get("junit_sha256") == _digest(members[junit]), "ORIGINAL_JUNIT_MISMATCH")
            _require(_equal(record.get("test_integrity"), _junit(members[junit])), "TEST_IDENTITY_RESULTS")
        else:
            _require(record.get("test_integrity") is None, "UNDECLARED_TEST_RESULTS")
        _require(evidence._command_status(command, record) == "PASS", "COMMAND_NOT_PASS")
    _require(output_root is not None, "ORIGINAL_OUTPUT_ROOT_UNOBSERVABLE")
    units = evidence._acceptance_results(suite, records)
    _require(_equal(artifact.get("units"), units), "AC_RESULTS_MISMATCH")
    _require(all(ac["verification_status"] == "PASS" for unit in units for ac in unit["acceptance"]),
             "AC_NOT_VERIFIED")
    return {"schema_version": "delivery-archive-verification-v1", "status": "INTEGRITY_VERIFIED",
            "observed_at": datetime.now(UTC).isoformat(), "archive_sha256": args.archive_sha256,
            "expectations": binding, "suite_path": args.suite, "original_binding": artifact["binding"],
            "original_environment": environment, "original_generated_at": artifact["generated_at"],
            "original_output_dir": output_root, "original_commands": records, "original_units": units,
            "verified_committed_files": committed, "claims": dict(_CLAIMS),
            "verification_machine": {"head_sha": git.text("rev-parse", "HEAD"),
                                     "platform": platform.platform(), "python": platform.python_version()},
            "limitations": ["Original commands were not rerun", "Execution source not authenticated",
                            "No Owner acceptance or runtime baseline established",
                            "Original collector check and historical failures remain unchanged"]}


class SafeParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise ArchiveError("INPUT_INVALID", 2)


def main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int:
    parser = SafeParser(description=__doc__)
    for name in ("archive", "report"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("archive-sha256", "repository", "head-sha", "base-sha", "tested-sha",
                 "tested-tree", "suite", "execution-kind", "run-url"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--repo-root", type=Path)
    try:
        args = parser.parse_args(argv)
        if (not _DIGEST.fullmatch(args.archive_sha256)
                or not all(_SHA.fullmatch(v) for v in (args.head_sha, args.base_sha, args.tested_sha, args.tested_tree))
                or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository)
                or args.execution_kind not in _SOURCES):
            raise ArchiveError("INPUT_INVALID", 2)
        valid_url = (re.fullmatch(r"local://offline/[A-Za-z0-9][A-Za-z0-9_.-]*", args.run_url)
                     if args.execution_kind == "local" else re.fullmatch(
                         rf"https://github.com/{re.escape(args.repository)}/actions/runs/[1-9][0-9]*(?:/attempts/[1-9][0-9]*)?", args.run_url))
        if not valid_url:
            raise ArchiveError("INPUT_INVALID", 2)
        try:
            args.suite = _relative(args.suite)
        except ArchiveError as exc:
            raise ArchiveError("INPUT_INVALID_SUITE_PATH", 2) from exc
        root = _host_path(repo_root or args.repo_root or _REPO_ROOT)
        report = _host_path(args.report)
        if report.exists() or report.is_relative_to(root) or not report.parent.is_dir():
            raise ArchiveError("REPORT_NOT_NEW_EXTERNAL_FILE", 2)
        result = _verify(args, root)
        _host_path(args.report)
        with report.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, ensure_ascii=False, allow_nan=False)
            handle.write("\n")
        print("verify_delivery_archive: INTEGRITY_VERIFIED (source unauthenticated)")
        return 0
    except ArchiveError as exc:
        label = "REJECTED" if exc.exit_code == 1 else "INPUT_OR_DEPENDENCY_ERROR"
        print(f"verify_delivery_archive: {label} ({exc})")
        return exc.exit_code
    except evidence.EvidenceError:
        print("verify_delivery_archive: REJECTED (INVALID_EXECUTION_EVIDENCE)")
        return 1
    except (OSError, ValueError, KeyError, TypeError, OverflowError, RecursionError, subprocess.TimeoutExpired):
        print("verify_delivery_archive: INPUT_OR_DEPENDENCY_ERROR (UNVERIFIED_INPUT)")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
