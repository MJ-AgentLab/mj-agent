"""Portable archive integrity tests with real isolated Git objects and fixed outcomes."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import stat
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/sdd/verify_delivery_archive.py"
XML = b'<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0"><testcase classname="probe" name="test_result"/></testsuite></testsuites>'
LOG = b"observed expected result\n"
ROOT = "/home/runner/work/evidence/original-output"
UNSAFE_ZIP_NAMES = ("../outside", "/absolute", "C:/drive", "x\\y", "a/../b",
                    ".env", "secrets.enc", "NUL.txt", "trailing.", "a//b", "folder/")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(repo: Path, *args: str, input_text: str | None = None) -> str:
    env = {k: v for k in (
        "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP",
    ) if (v := os.environ.get(k)) is not None}
    env.update({"GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"})
    result = subprocess.run(["git", "--no-replace-objects", "-C", str(repo), *args],
                            env=env, input=input_text, capture_output=True, text=True, check=True)
    return result.stdout.strip()


@dataclass
class Case:
    repo: Path
    archive: Path
    report: Path
    artifact: dict[str, Any]
    members: dict[str, bytes]

    def pack(self) -> None:
        self.members["delivery.json"] = (json.dumps(self.artifact) + "\n").encode()
        with zipfile.ZipFile(self.archive, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in self.members.items():
                archive.writestr(name, data)

    def args(self) -> list[str]:
        binding = self.artifact["binding"]
        result = ["--archive", str(self.archive), "--archive-sha256",
                  digest(self.archive.read_bytes()), "--suite", "suite.json",
                  "--report", str(self.report), "--repo-root", str(self.repo)]
        for flag, key in (("repository", "repository"), ("head-sha", "head_sha"),
                          ("base-sha", "base_sha"), ("tested-sha", "tested_sha"),
                          ("tested-tree", "tested_tree"), ("execution-kind", "execution_kind"),
                          ("run-url", "run_url")):
            result.extend(["--" + flag, binding[key]])
        return result


@pytest.fixture
def case(tmp_path: Path) -> Case:
    repo = tmp_path / "repo"
    repo.mkdir()
    suite = {
        "schema_version": 1, "harness": ["harness.py"], "dependencies": ["lock.txt"],
        "commands": [{"id": "probe", "argv": ["python", "probe.py", "{output_dir}/probe.xml",
                                               "--log={output_dir}/probe.log", "--root", "."],
                      "expected_exit": 0, "junit": "probe.xml", "min_tests": 1}],
        "units": [{"id": "pilot", "baseline": ["baseline.md"], "inputs": ["input.json"],
                   "acceptance": [{"id": "AC-1", "expected": "observed expected result",
                                   "mode": "SELFTEST_SOFTWARE", "source_kind": "synthetic_fixture",
                                   "command_ids": ["probe"],
                                   "tests": [{"command_id": "probe", "ids": ["probe::test_result"]}]}]}],
    }
    files = {"harness.py": b"# fixed harness\n", "probe.py": b"# original command\n",
             "lock.txt": b"no dependencies\n", "baseline.md": b"AC-1 fixed baseline\n",
             "input.json": b'{"expected":"observed"}\n', "suite.json": json.dumps(suite).encode()}
    for name, data in files.items():
        (repo / name).write_bytes(data)
    git(repo, "init", "--quiet")
    git(repo, "config", "core.autocrlf", "false")
    base = git(repo, "commit-tree", git(repo, "mktree", input_text=""), input_text="base\n")
    git(repo, "add", "--", *files)
    tree = git(repo, "write-tree")
    head = git(repo, "commit-tree", tree, "-p", base, input_text="tested\n")
    newer = git(repo, "commit-tree", tree, "-p", head, input_text="verifier checkout differs\n")
    git(repo, "update-ref", "HEAD", newer)
    hashes = {name: digest(data) for name, data in files.items()}
    integrity = {"tests": 1, "passed": 1, "failed": 0, "skipped": 0,
                 "cases": {"probe::test_result": "PASS"}}
    ac = suite["units"][0]["acceptance"][0]
    artifact = {
        "schema_version": "delivery-evidence-v1",
        "binding": {"repository": "fixture/repo", "head_sha": head, "base_sha": base,
                    "tested_sha": head, "tested_tree": tree, "tracked_worktree_clean": True,
                    "execution_kind": "local", "run_url": "local://offline/original-123"},
        "digests": {"suite_path": "suite.json", "suite_sha256": hashes["suite.json"],
                    "harness": {"harness.py": hashes["harness.py"]},
                    "dependencies": {"lock.txt": hashes["lock.txt"]},
                    "units": {"pilot": {"baseline": {"baseline.md": hashes["baseline.md"]},
                                        "inputs": {"input.json": hashes["input.json"]}}}},
        "committed_files": hashes, "execution_source": "LOCAL_OFFLINE_RUNTIME",
        "claims": {"owner_accepted": False, "runtime_baseline_eligible": False,
                   "independent_source_authenticated": False},
        "environment": {"python": "3.13.1", "platform": "Linux-original-execution"},
        "generated_at": "2026-10-01T00:00:02+00:00",
        "commands": [{"id": "probe", "argv": suite["commands"][0]["argv"],
                      "resolved_argv": ["python", "probe.py", ROOT + "/probe.xml",
                                        "--log=" + ROOT + "/probe.log", "--root", "."],
                      "expected_exit": 0, "exit_code": 0, "execution_error": None,
                      "started_at": "2026-10-01T00:00:00+00:00",
                      "finished_at": "2026-10-01T00:00:01+00:00",
                      "run_url": "local://offline/original-123", "output_ref": "probe.log",
                      "output_sha256": digest(LOG), "junit_ref": "probe.xml",
                      "junit_sha256": digest(XML), "test_integrity": integrity}],
        "units": [{"id": "pilot", "acceptance": [{**ac, "status": "SELFTEST",
                  "verification_status": "PASS", "actual": [{"command_id": "probe",
                  "expected_exit": 0, "exit_code": 0, "status": "PASS",
                  "tests": {"probe::test_result": "PASS"}, "output_ref": "probe.log"}]}]}],
    }
    result = Case(repo, tmp_path / "original.zip", tmp_path / "report.json", artifact,
                  {"probe.log": LOG, "probe.xml": XML})
    result.pack()
    return result


def verify(case: Case, args: list[str] | None = None) -> int:
    module = importlib.import_module("scripts.sdd.verify_delivery_archive")
    return module.main(args or case.args(), repo_root=case.repo)


def test_original_layout_and_git_version_survive_relocation(case: Case) -> None:
    original = case.archive.read_bytes()
    assert verify(case) == 0
    report = json.loads(case.report.read_text())
    assert report["status"] == "INTEGRITY_VERIFIED"
    assert report["original_output_dir"] == ROOT
    assert report["original_binding"] == case.artifact["binding"]
    assert report["verification_machine"]["head_sha"] == git(case.repo, "rev-parse", "HEAD")
    assert report["verification_machine"]["head_sha"] != case.artifact["binding"]["tested_sha"]
    assert report["claims"] == case.artifact["claims"]
    assert case.archive.read_bytes() == original


def test_real_cli_rejects_explicit_wrong_tree(case: Case) -> None:
    args = case.args()
    args[args.index("--tested-tree") + 1] = "f" * 40
    result = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    assert result.returncode == 1
    assert "REJECTED" in result.stdout
    assert not case.report.exists()


def test_real_cli_verifies_without_running_candidate_commands(case: Case) -> None:
    (case.repo / "probe.py").write_text("raise RuntimeError('must not run')\n")
    result = subprocess.run([sys.executable, str(SCRIPT), *case.args()],
                            capture_output=True, text=True)
    assert result.returncode == 0
    assert case.report.is_file()


@pytest.mark.parametrize("mutation", [
    "binding", "source", "claim", "claim_integer", "baseline", "blob", "argv",
    "resolved_argv", "exit", "expected_exit", "time", "environment", "log", "junit",
    "missing_case", "duplicate_case", "skip", "fail", "test_integrity", "ac", "extra_member",
])
def test_version_content_results_and_claims_cannot_be_forged(case: Case, mutation: str) -> None:
    args = case.args()
    artifact = case.artifact
    record = artifact["commands"][0]
    if mutation == "binding":
        artifact["binding"]["head_sha"] = "d" * 40
    elif mutation == "source":
        artifact["execution_source"] = "GITHUB_ACTIONS_UNAUTHENTICATED"
    elif mutation in {"claim", "claim_integer"}:
        artifact["claims"]["owner_accepted"] = True if mutation == "claim" else 0
    elif mutation == "baseline":
        artifact["digests"]["units"]["pilot"]["baseline"]["baseline.md"] = "0" * 64
    elif mutation == "blob":
        artifact["committed_files"]["probe.py"] = "0" * 64
    elif mutation == "argv":
        record["argv"][0] = "not-original-python"
    elif mutation == "resolved_argv":
        record["resolved_argv"][0] = "not-original-python"
    elif mutation == "exit":
        record["exit_code"] = 1
    elif mutation == "expected_exit":
        record["expected_exit"] = True
    elif mutation == "time":
        record["finished_at"] = "2026-10-02T00:00:00+00:00"
    elif mutation == "environment":
        artifact["environment"]["platform"] = ""
    elif mutation == "log":
        case.members["probe.log"] = b"forged log\n"
    elif mutation == "junit":
        case.members["probe.xml"] = XML + b"changed"
    elif mutation in {"missing_case", "duplicate_case", "skip", "fail"}:
        xml = {
            "missing_case": b'<testsuite tests="1" failures="0" errors="0" skipped="0"/>',
            "duplicate_case": b'<testsuite tests="2" failures="0" errors="0" skipped="0"><testcase classname="probe" name="test_result"/><testcase classname="probe" name="test_result"/></testsuite>',
            "skip": b'<testsuite tests="1" failures="0" errors="0" skipped="1"><testcase classname="probe" name="test_result"><skipped/></testcase></testsuite>',
            "fail": b'<testsuite tests="1" failures="1" errors="0" skipped="0"><testcase classname="probe" name="test_result"><failure/></testcase></testsuite>',
        }[mutation]
        case.members["probe.xml"] = xml
        record["junit_sha256"] = digest(xml)
    elif mutation == "test_integrity":
        record["test_integrity"]["cases"]["probe::invented"] = "PASS"
    elif mutation == "ac":
        artifact["units"][0]["acceptance"][0]["status"] = "PASS"
    else:
        case.members["undeclared.log"] = b"not declared"
    case.pack()
    args[args.index("--archive-sha256") + 1] = digest(case.archive.read_bytes())
    assert verify(case, args) == 1
    assert not case.report.exists()


@pytest.mark.parametrize("name", UNSAFE_ZIP_NAMES)
def test_unsafe_zip_members_are_never_extracted(case: Case, name: str) -> None:
    case.members[name] = b"synthetic forbidden-name fixture"
    case.pack()
    assert verify(case) == 1
    assert not case.report.exists()


def test_duplicate_and_link_members_are_rejected(case: Case) -> None:
    with zipfile.ZipFile(case.archive, "a") as archive:
        with pytest.warns(UserWarning, match="Duplicate name"):
            archive.writestr("probe.log", LOG)
    assert verify(case) == 1
    case.pack()
    link = zipfile.ZipInfo("link")
    link.create_system = 3
    link.external_attr = 0o120777 << 16
    with zipfile.ZipFile(case.archive, "a") as archive:
        archive.writestr(link, b"probe.log")
    assert verify(case) == 1


def test_archive_digest_and_missing_tested_object_fail_closed(case: Case) -> None:
    args = case.args()
    args[args.index("--archive-sha256") + 1] = "0" * 64
    assert verify(case, args) == 1
    args = case.args()
    args[args.index("--tested-sha") + 1] = "f" * 40
    assert verify(case, args) == 2
    assert not case.report.exists()


@pytest.mark.parametrize("reverse", [False, True])
def test_exact_merge_parent_order_is_required(case: Case, reverse: bool) -> None:
    binding = case.artifact["binding"]
    parents = [binding["base_sha"], binding["head_sha"]]
    if reverse:
        parents.reverse()
    tested = git(case.repo, "commit-tree", binding["tested_tree"], "-p", parents[0],
                 "-p", parents[1], input_text="PR merge object\n")
    binding["tested_sha"] = tested
    case.pack()
    assert verify(case) == (1 if reverse else 0)


def test_report_is_exclusive_and_secret_paths_are_not_opened(case: Case) -> None:
    case.report.write_bytes(b"must remain\n")
    assert verify(case) == 2
    assert case.report.read_bytes() == b"must remain\n"
    args = case.args()
    args[args.index("--archive") + 1] = str(case.archive.parent / ".env")
    assert verify(case, args) == 2


def test_global_git_environment_cannot_redirect_object_reads(case: Case, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_DIR", str(case.repo / "does-not-exist"))
    monkeypatch.setenv("GIT_WORK_TREE", str(case.repo / "wrong"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(case.repo / "wrong-index"))
    assert verify(case) == 0


def test_cli_errors_do_not_echo_untrusted_payload(case: Case) -> None:
    args = case.args()
    args[args.index("--execution-kind") + 1] = "UNTRUSTED_PAYLOAD_MUST_NOT_APPEAR"
    result = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    assert result.returncode == 2
    assert "UNTRUSTED_PAYLOAD_MUST_NOT_APPEAR" not in result.stdout + result.stderr


def test_mixed_original_output_roots_are_rejected(case: Case) -> None:
    case.artifact["commands"][0]["resolved_argv"][-1] = "--log=/different/output/probe.log"
    case.pack()
    assert verify(case) == 1
    assert not case.report.exists()


@pytest.mark.parametrize("output_root", [r"C:\original\output", "/original/output"])
def test_native_original_root_characters_are_preserved(case: Case, output_root: str) -> None:
    record = case.artifact["commands"][0]
    record["resolved_argv"] = [value.replace("{output_dir}", output_root) for value in record["argv"]]
    case.pack()
    assert verify(case) == 0
    report = json.loads(case.report.read_text())
    assert report["original_output_dir"] == output_root
    assert report["original_commands"][0]["resolved_argv"] == record["resolved_argv"]


@pytest.mark.parametrize("output_root", [r"C:\original\\output", r"C:\original\.\output",
                                       r"C:\original\..\output", "//host/share/output"])
def test_ambiguous_original_roots_are_rejected(case: Case, output_root: str) -> None:
    record = case.artifact["commands"][0]
    record["resolved_argv"] = [value.replace("{output_dir}", output_root) for value in record["argv"]]
    case.pack()
    assert verify(case) == 1


@pytest.mark.parametrize("limit, value, rejection", [
    ("MAX_ARCHIVE_BYTES", 1, "ARCHIVE_SIZE_LIMIT"),
    ("MAX_MEMBER_BYTES", 2000, "ZIP_MEMBER_SIZE_LIMIT"),
    ("MAX_TOTAL_BYTES", 1, "ZIP_TOTAL_SIZE_LIMIT"),
    ("MAX_MEMBERS", 2, "ZIP_MEMBER_LIMIT"),
])
def test_archive_resource_limits_fail_without_a_report(case: Case, monkeypatch: pytest.MonkeyPatch,
                                                     limit: str, value: int, rejection: str,
                                                     capsys: pytest.CaptureFixture[str]) -> None:
    module = importlib.import_module("scripts.sdd.verify_delivery_archive")
    monkeypatch.setattr(module, limit, value)
    assert verify(case) == 1
    assert rejection in capsys.readouterr().out
    assert not case.report.exists()


def test_windows_reparse_ancestor_is_rejected_before_archive_read(case: Case,
                                                                monkeypatch: pytest.MonkeyPatch) -> None:
    original_lstat = Path.lstat

    class ReparseMetadata:
        st_mode = stat.S_IFDIR
        st_file_attributes = 0x400

    def lstat(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path == case.archive.parent:
            return ReparseMetadata()
        return original_lstat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", lstat)
    assert verify(case) == 2
    assert not case.report.exists()


def test_nonancestor_base_is_an_integrity_rejection(case: Case) -> None:
    binding = case.artifact["binding"]
    binding["base_sha"] = git(case.repo, "commit-tree", binding["tested_tree"],
                              input_text="unrelated base\n")
    case.pack()
    assert verify(case) == 1


def test_malformed_junit_count_is_an_integrity_rejection(case: Case) -> None:
    xml = XML.replace(b'tests="1"', b'tests="untrusted-count"')
    case.members["probe.xml"] = xml
    case.artifact["commands"][0]["junit_sha256"] = digest(xml)
    case.pack()
    assert verify(case) == 1


def test_replace_ref_cannot_supply_an_equivalent_tested_object(case: Case) -> None:
    binding = case.artifact["binding"]
    original_head = binding["head_sha"]
    empty_tree = git(case.repo, "mktree", input_text="")
    impostor = git(case.repo, "commit-tree", empty_tree, "-p", binding["base_sha"],
                   input_text="different real object\n")
    git(case.repo, "replace", impostor, original_head)
    binding["head_sha"] = binding["tested_sha"] = impostor
    case.pack()
    assert verify(case) == 1
    assert not case.report.exists()


def test_git_timeout_is_a_safe_dependency_failure(case: Case, monkeypatch: pytest.MonkeyPatch,
                                               capsys: pytest.CaptureFixture[str]) -> None:
    module = importlib.import_module("scripts.sdd.verify_delivery_archive")

    def timed_out(*args: Any, **kwargs: Any) -> Any:
        raise subprocess.TimeoutExpired("untrusted-argument", kwargs["timeout"],
                                        output="UNTRUSTED_GIT_OUTPUT", stderr="UNTRUSTED_GIT_ERROR")

    monkeypatch.setattr(module.subprocess, "run", timed_out)
    assert verify(case) == 2
    observed = capsys.readouterr()
    assert "UNTRUSTED" not in observed.out + observed.err
    assert not case.report.exists()


def test_utf16_junit_entity_declarations_are_rejected(case: Case) -> None:
    xml = ('<?xml version="1.0" encoding="UTF-16"?>'
           '<!DOCTYPE testsuite [<!ENTITY result "test_result">]>'
           '<testsuite tests="1" failures="0" errors="0" skipped="0">'
           '<testcase classname="probe" name="&result;"/></testsuite>').encode("utf-16")
    case.members["probe.xml"] = xml
    case.artifact["commands"][0]["junit_sha256"] = digest(xml)
    case.pack()
    assert verify(case) == 1
    assert not case.report.exists()


def test_utf16_junit_without_declarations_preserves_original_bytes(case: Case) -> None:
    xml = XML.decode().encode("utf-16")
    case.members["probe.xml"] = xml
    case.artifact["commands"][0]["junit_sha256"] = digest(xml)
    case.pack()
    original = case.archive.read_bytes()
    assert verify(case) == 0
    assert case.archive.read_bytes() == original
