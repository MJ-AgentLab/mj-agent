"""Offline evidence integrity checks against injected temporary repositories."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from scripts.sdd import delivery_evidence as evidence

HEAD = "1" * 40
BASE = "2" * 40
TREE = "3" * 40


@pytest.fixture
def evidence_case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "baseline.md").write_text("AC-1: observes the expected result\n", encoding="utf-8")
    (repo / "harness.py").write_text("# Controlled harness definition\n", encoding="utf-8")
    (repo / "lock.txt").write_text("no external dependencies\n", encoding="utf-8")
    (repo / "input.json").write_text('{"expected": "observed"}\n', encoding="utf-8")
    (repo / "probe.py").write_text(
        "import pathlib, sys\n"
        "pathlib.Path(sys.argv[1]).write_text(\n"
        "    '<testsuites><testsuite tests=\"1\" failures=\"0\" errors=\"0\" skipped=\"0\">'\n"
        "    '<testcase classname=\"probe\" name=\"test_result\"/>'\n"
        "    '</testsuite></testsuites>', encoding='utf-8')\n"
        "print('observed expected result')\n",
        encoding="utf-8",
    )
    suite = {
        "schema_version": 1,
        "harness": ["harness.py", "probe.py"],
        "dependencies": ["lock.txt"],
        "commands": [{
            "id": "probe", "argv": [sys.executable, "probe.py", "{output_dir}/probe.xml"],
            "expected_exit": 0, "junit": "probe.xml", "min_tests": 1,
        }],
        "units": [{
            "id": "pilot", "baseline": ["baseline.md"], "inputs": ["input.json"],
            "acceptance": [{
                "id": "AC-1", "expected": "observed expected result", "command_ids": ["probe"],
                "mode": "SELFTEST_SOFTWARE", "source_kind": "synthetic_fixture",
                "tests": [{"command_id": "probe", "ids": ["probe::test_result"]}],
            }],
        }],
    }
    suite_path = repo / "suite.json"
    suite_path.write_text(json.dumps(suite), encoding="utf-8")
    monkeypatch.setattr(evidence, "git_identity", lambda _: {
        "tested_sha": HEAD, "tested_tree": TREE, "tracked_worktree_clean": True,
    })
    monkeypatch.setattr(evidence, "validate_git_relationship", lambda *_: None, raising=False)
    monkeypatch.setattr(evidence, "validate_checkout_inputs", lambda *_: None, raising=False)
    return repo, suite_path, tmp_path / "artifact"


def _arguments(action: str, suite: Path, output: Path) -> list[str]:
    return [action, "--suite", str(suite), "--output-dir", str(output),
            "--repository", "test/repo", "--head-sha", HEAD, "--base-sha", BASE,
            "--execution-kind", "local", "--run-url", "local://offline/fixture-123"]


def _run(case: tuple[Path, Path, Path]) -> dict:
    repo, suite, output = case
    assert evidence.main(_arguments("run", suite, output), repo_root=repo) == 0
    return json.loads((output / "delivery.json").read_text(encoding="utf-8"))


def test_real_command_output_binds_versions_and_selftest(evidence_case: tuple[Path, Path, Path]) -> None:
    repo, suite, output = evidence_case
    artifact = _run(evidence_case)
    assert artifact["binding"]["tested_sha"] == HEAD
    assert artifact["binding"]["tested_tree"] == TREE
    assert artifact["binding"]["base_sha"] == BASE
    assert artifact["binding"]["execution_kind"] == "local"
    assert artifact["execution_source"] == "LOCAL_OFFLINE_RUNTIME"
    assert artifact["units"][0]["acceptance"][0]["status"] == "SELFTEST"
    assert artifact["units"][0]["acceptance"][0]["actual"][0]["tests"] == {
        "probe::test_result": "PASS",
    }
    assert artifact["claims"] == {
        "runtime_baseline_eligible": False, "owner_accepted": False,
        "independent_source_authenticated": False,
    }
    assert "observed expected result" in (output / "probe.log").read_text(encoding="utf-8")
    assert evidence.main(_arguments("check", suite, output), repo_root=repo) == 0


@pytest.mark.parametrize("mutation", ["missing", "wrong_head", "wrong_base", "wrong_tree",
                                     "missing_log", "fake_pass", "false_claim"])
def test_missing_mismatched_and_forged_evidence_block(
    evidence_case: tuple[Path, Path, Path], mutation: str,
) -> None:
    repo, suite, output = evidence_case
    artifact = _run(evidence_case)
    if mutation == "missing":
        (output / "delivery.json").unlink()
    elif mutation == "missing_log":
        (output / "probe.log").unlink()
    else:
        if mutation.startswith("wrong_"):
            field = {"wrong_head": "head_sha", "wrong_base": "base_sha", "wrong_tree": "tested_tree"}[mutation]
            artifact["binding"][field] = "4" * 40
        elif mutation == "fake_pass":
            artifact["commands"][0]["exit_code"] = 1
            artifact["units"][0]["acceptance"][0]["status"] = "PASS"
        else:
            artifact["claims"]["owner_accepted"] = True
        (output / "delivery.json").write_text(json.dumps(artifact), encoding="utf-8")
    assert evidence.main(_arguments("check", suite, output), repo_root=repo) == 1


def test_changed_acceptance_baseline_invalidates_evidence(evidence_case: tuple[Path, Path, Path]) -> None:
    repo, suite, output = evidence_case
    _run(evidence_case)
    (repo / "baseline.md").write_text("AC-1 changed\n", encoding="utf-8")
    assert evidence.main(_arguments("check", suite, output), repo_root=repo) == 1


@pytest.mark.parametrize("xml", [
    '<testsuite tests="0" failures="0" errors="0" skipped="0"/>',
    '<testsuite tests="1" failures="0" errors="0" skipped="1"><testcase classname="probe" name="test_result"><skipped/></testcase></testsuite>',
    '<testsuite tests="1" failures="0" errors="0" skipped="0"><testcase classname="probe" name="other"/></testsuite>',
    '<testsuite tests="2" failures="0" errors="0" skipped="0"><testcase classname="probe" name="test_result"/></testsuite>',
    '<testsuite tests="2" failures="0" errors="0" skipped="0"><testcase classname="probe" name="test_result"/><testcase classname="probe" name="test_result"/></testsuite>',
    '<testsuite tests="1" failures="0" errors="0" skipped="0"><testcase classname="probe" name="test_result"><failure/></testcase></testsuite>',
    '<broken',
])
def test_process_zero_cannot_hide_incomplete_or_failed_tests(
    evidence_case: tuple[Path, Path, Path], xml: str,
) -> None:
    repo, suite, output = evidence_case
    (repo / "probe.py").write_text(
        "import pathlib, sys\n"
        f"pathlib.Path(sys.argv[1]).write_text({xml!r}, encoding='utf-8')\n",
        encoding="utf-8",
    )
    assert evidence.main(_arguments("run", suite, output), repo_root=repo) == 1
    artifact = json.loads((output / "delivery.json").read_text(encoding="utf-8"))
    assert artifact["units"][0]["acceptance"][0]["status"] != "PASS"
    assert artifact["units"][0]["acceptance"][0]["status"] != "SELFTEST"


def test_expected_nonzero_selftest_exit_is_preserved(evidence_case: tuple[Path, Path, Path]) -> None:
    repo, suite, _ = evidence_case
    payload = json.loads(suite.read_text(encoding="utf-8"))
    payload["commands"][0]["expected_exit"] = 3
    suite.write_text(json.dumps(payload), encoding="utf-8")
    with (repo / "probe.py").open("a", encoding="utf-8") as stream:
        stream.write("sys.exit(3)\n")
    assert _run(evidence_case)["commands"][0]["exit_code"] == 3


def test_artifact_must_be_outside_checkout_and_never_overwrite(evidence_case: tuple[Path, Path, Path]) -> None:
    repo, suite, output = evidence_case
    assert evidence.main(_arguments("run", suite, repo / "output"), repo_root=repo) == 1
    _run(evidence_case)
    assert evidence.main(_arguments("run", suite, output), repo_root=repo) == 2


def test_secret_input_is_rejected_before_read(evidence_case: tuple[Path, Path, Path]) -> None:
    repo, suite, output = evidence_case
    payload = json.loads(suite.read_text(encoding="utf-8"))
    payload["units"][0]["inputs"] = [".env"]
    suite.write_text(json.dumps(payload), encoding="utf-8")
    assert evidence.main(_arguments("run", suite, output), repo_root=repo) == 2
    assert not output.exists()


def test_synthetic_cannot_claim_actual_behavior(evidence_case: tuple[Path, Path, Path]) -> None:
    repo, suite, output = evidence_case
    payload = json.loads(suite.read_text(encoding="utf-8"))
    payload["units"][0]["acceptance"][0]["mode"] = "BEHAVIOR"
    suite.write_text(json.dumps(payload), encoding="utf-8")
    assert evidence.main(_arguments("run", suite, output), repo_root=repo) == 2


def test_invalid_suite_schema_returns_usage_error(evidence_case: tuple[Path, Path, Path]) -> None:
    repo, suite, output = evidence_case
    suite.write_text('{"schema_version": "unsupported"}', encoding="utf-8")
    assert evidence.main(_arguments("run", suite, output), repo_root=repo) == 2
    assert not output.exists()


def test_missing_command_returns_execution_error(evidence_case: tuple[Path, Path, Path]) -> None:
    repo, suite, output = evidence_case
    payload = json.loads(suite.read_text(encoding="utf-8"))
    payload["commands"][0]["argv"] = ["mj-agent-deliberately-missing-test-command"]
    suite.write_text(json.dumps(payload), encoding="utf-8")
    assert evidence.main(_arguments("run", suite, output), repo_root=repo) == 2
    artifact = json.loads((output / "delivery.json").read_text(encoding="utf-8"))
    assert artifact["units"][0]["acceptance"][0]["verification_status"] == "FAIL"


@pytest.mark.parametrize("path", ["harness.py", "lock.txt", "input.json"])
def test_changed_definition_dependency_or_input_invalidates_evidence(
    evidence_case: tuple[Path, Path, Path], path: str,
) -> None:
    repo, suite, output = evidence_case
    _run(evidence_case)
    (repo / path).write_text("changed\n", encoding="utf-8")
    assert evidence.main(_arguments("check", suite, output), repo_root=repo) == 1


def test_dirty_checkout_cannot_claim_tested_commit(
    evidence_case: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, suite, output = evidence_case
    monkeypatch.setattr(evidence, "git_identity", lambda _: {
        "tested_sha": HEAD, "tested_tree": TREE, "tracked_worktree_clean": False,
    })
    assert evidence.main(_arguments("run", suite, output), repo_root=repo) == 1
    assert not output.exists()


@pytest.mark.parametrize("component", [
    ".env::$DATA", "ordinary:stream", "ordinary::$DATA", ".env ", ".env.",
    "ordinary ", "ordinary.", "CON", "NUL.txt", "LPT1.log", "file?name", "file\x01name",
])
def test_windows_aliases_are_rejected_before_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, component: str,
) -> None:
    def forbidden_metadata(_: Path) -> None:
        pytest.fail("path metadata accessed before rejecting a forbidden Windows spelling")

    monkeypatch.setattr(Path, "lstat", forbidden_metadata)
    with pytest.raises(evidence.EvidenceError):
        evidence._safe_path(tmp_path / component)


def _temporary_git(repo: Path, *arguments: str, input_text: str | None = None) -> str:
    # Isolated disposable object graph; no project refs, credentials or hooks.
    env = {name: value for name in ("PATH", "SYSTEMROOT", "WINDIR", "HOME")
           if (value := os.environ.get(name)) is not None}
    env.update({"GIT_AUTHOR_NAME": "Evidence Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                "GIT_COMMITTER_NAME": "Evidence Fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
                "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+0000",
                "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+0000"})
    result = subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false", *arguments],
                            input=input_text, capture_output=True, text=True, env=env, check=True)
    return result.stdout.strip()


@pytest.fixture
def git_graph(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    repo = tmp_path / "ordinary-git-fixture"
    repo.mkdir()
    _temporary_git(repo, "init", "--quiet")
    tree = _temporary_git(repo, "mktree", input_text="")
    base = _temporary_git(repo, "commit-tree", tree, input_text="base\n")
    head = _temporary_git(repo, "commit-tree", tree, "-p", base, input_text="head\n")
    unrelated = _temporary_git(repo, "commit-tree", tree, input_text="unrelated\n")
    merge = _temporary_git(repo, "commit-tree", tree, "-p", base, "-p", head, input_text="merge\n")
    reversed_merge = _temporary_git(repo, "commit-tree", tree, "-p", head, "-p", base,
                                    input_text="reversed\n")
    _temporary_git(repo, "update-ref", "HEAD", head)
    return repo, {"base": base, "head": head, "unrelated": unrelated,
                  "merge": merge, "reversed_merge": reversed_merge}


@pytest.mark.parametrize("tested", ["head", "merge"])
def test_binding_accepts_only_real_head_or_exact_pr_merge(
    git_graph: tuple[Path, dict[str, str]], tested: str,
) -> None:
    repo, commits = git_graph
    _temporary_git(repo, "update-ref", "HEAD", commits[tested])
    args = argparse.Namespace(repository="test/repo", head_sha=commits["head"],
                              base_sha=commits["base"],
                              run_url="https://github.com/test/repo/actions/runs/123")
    binding = evidence._binding(args, repo)
    assert binding["tested_sha"] == commits[tested]
    assert binding["head_sha"] == commits["head"]


@pytest.mark.parametrize("invalid", ["unrelated_tested", "unrelated_base", "missing_base",
                                   "missing_head", "reversed_merge"])
def test_binding_rejects_arbitrary_missing_and_unrelated_commit_claims(
    git_graph: tuple[Path, dict[str, str]], invalid: str,
) -> None:
    repo, commits = git_graph
    tested = commits["head"]
    base, head = commits["base"], commits["head"]
    if invalid == "unrelated_tested":
        tested = commits["unrelated"]
    elif invalid == "unrelated_base":
        base = commits["unrelated"]
    elif invalid == "missing_base":
        base = "9" * 40
    elif invalid == "missing_head":
        head = "9" * 40
    else:
        tested = commits["reversed_merge"]
    _temporary_git(repo, "update-ref", "HEAD", tested)
    args = argparse.Namespace(repository="test/repo", head_sha=head, base_sha=base,
                              run_url="https://github.com/test/repo/actions/runs/123")
    with pytest.raises(evidence.EvidenceError):
        evidence._binding(args, repo)


@pytest.mark.parametrize("change", ["dirty", "sha", "tree"])
def test_candidate_change_during_execution_invalidates_run(
    evidence_case: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch, change: str,
) -> None:
    repo, suite, output = evidence_case
    original = {"tested_sha": HEAD, "tested_tree": TREE, "tracked_worktree_clean": True}
    changed = {**original, {"dirty": "tracked_worktree_clean", "sha": "tested_sha",
                           "tree": "tested_tree"}[change]: False if change == "dirty" else "4" * 40}
    identities = iter((original, changed))
    monkeypatch.setattr(evidence, "git_identity", lambda _: next(identities))
    assert evidence.main(_arguments("run", suite, output), repo_root=repo) == 1
    assert not (output / "delivery.json").exists()


@pytest.mark.parametrize(("kind", "url"), [
    ("local", "https://github.com/test/repo/actions/runs/123"),
    ("github-actions", "local://offline/fixture-123"),
    ("local", "local://offline/../escape"),
    ("local", "local://offline/run?credential=forbidden"),
])
def test_execution_kind_rejects_cross_source_and_noncanonical_urls(
    evidence_case: tuple[Path, Path, Path], kind: str, url: str,
) -> None:
    repo, suite, output = evidence_case
    args = _arguments("run", suite, output)
    args[args.index("--execution-kind") + 1] = kind
    args[args.index("--run-url") + 1] = url
    assert evidence.main(args, repo_root=repo) == 2
    assert not output.exists()


@pytest.mark.parametrize("mutation", ["source", "kind"])
def test_local_artifact_cannot_be_relabelled_as_cloud_execution(
    evidence_case: tuple[Path, Path, Path], mutation: str,
) -> None:
    repo, suite, output = evidence_case
    artifact = _run(evidence_case)
    if mutation == "source":
        artifact["execution_source"] = "GITHUB_ACTIONS_UNAUTHENTICATED"
    else:
        artifact["binding"]["execution_kind"] = "github-actions"
    (output / "delivery.json").write_text(json.dumps(artifact), encoding="utf-8")
    assert evidence.main(_arguments("check", suite, output), repo_root=repo) == 1


def _real_candidate(
    case: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
) -> tuple[list[str], str]:
    repo, suite, output = case
    monkeypatch.undo()
    _temporary_git(repo, "init", "--quiet")
    # Match working bytes to the fixture's committed bytes, without global config.
    _temporary_git(repo, "config", "core.autocrlf", "false")
    empty_tree = _temporary_git(repo, "mktree", input_text="")
    base = _temporary_git(repo, "commit-tree", empty_tree, input_text="ordinary base\n")
    tracked = ["baseline.md", "harness.py", "lock.txt", "input.json", "probe.py", "suite.json"]
    if (repo / ".gitignore").exists():
        tracked.append(".gitignore")
    if (repo / ".gitattributes").exists():
        tracked.append(".gitattributes")
    _temporary_git(repo, "add", "--", *tracked)
    tree = _temporary_git(repo, "write-tree")
    head = _temporary_git(repo, "commit-tree", tree, "-p", base, input_text="ordinary candidate\n")
    _temporary_git(repo, "update-ref", "HEAD", head)
    arguments = _arguments("run", suite, output)
    arguments[arguments.index("--head-sha") + 1] = head
    arguments[arguments.index("--base-sha") + 1] = base
    return arguments, head


def test_untracked_bound_input_and_executed_script_cannot_claim_the_commit(
    evidence_case: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, suite, output = evidence_case
    # Ordinary first-party fixture only: no secret file is created or opened.
    (repo / "untracked_input.py").write_text((repo / "probe.py").read_text(encoding="utf-8"),
                                             encoding="utf-8")
    payload = json.loads(suite.read_text(encoding="utf-8"))
    payload["units"][0]["inputs"].append("untracked_input.py")
    payload["commands"][0]["argv"][1] = "untracked_input.py"
    suite.write_text(json.dumps(payload), encoding="utf-8")
    arguments, _ = _real_candidate(evidence_case, monkeypatch)
    assert evidence.git_identity(repo)["tracked_worktree_clean"] is True
    assert evidence.main(arguments, repo_root=repo) == 1
    assert not output.exists()


def test_ignored_shadow_python_module_cannot_hide_outside_the_tree(
    evidence_case: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _, output = evidence_case
    (repo / ".gitignore").write_text("shadow.py\n", encoding="utf-8")
    (repo / "shadow.py").write_text("# Harmless fixture; must never be imported.\n", encoding="utf-8")
    arguments, _ = _real_candidate(evidence_case, monkeypatch)
    assert evidence.main(arguments, repo_root=repo) == 1
    assert not output.exists()


def test_unbound_noncode_material_does_not_require_blanket_cleanliness(
    evidence_case: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _, _ = evidence_case
    (repo / "notes.md").write_text("Unrelated retained material\n", encoding="utf-8")
    (repo / ".playwright").mkdir()
    (repo / ".playwright" / "trace.json").write_text("{}\n", encoding="utf-8")
    arguments, _ = _real_candidate(evidence_case, monkeypatch)
    assert evidence.main(arguments, repo_root=repo) == 0


def test_explicit_ignored_dependency_and_cache_paths_can_remain(
    evidence_case: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _, _ = evidence_case
    (repo / ".gitignore").write_text(".venv/\n__pycache__/\n", encoding="utf-8")
    for path in (repo / ".venv" / "installed.py", repo / "__pycache__" / "probe.pyc"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Harmless ignored fixture, never imported\n", encoding="utf-8")
    arguments, _ = _real_candidate(evidence_case, monkeypatch)
    assert evidence.main(arguments, repo_root=repo) == 0


def test_working_digest_alone_cannot_replace_the_committed_blob(
    evidence_case: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, suite, _ = evidence_case
    _, head = _real_candidate(evidence_case, monkeypatch)
    (repo / "input.json").write_text('{"changed": true}\n', encoding="utf-8")
    definition, digests = evidence.load_suite(suite, repo)
    with pytest.raises(evidence.EvidenceError):
        evidence.validate_checkout_inputs(repo, head, definition, digests)


def test_repository_command_script_requires_its_own_committed_binding(
    evidence_case: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, suite, output = evidence_case
    (repo / "untracked_command.sh").write_text("# Harmless fixture, never executed\n", encoding="utf-8")
    payload = json.loads(suite.read_text(encoding="utf-8"))
    payload["commands"][0]["argv"] = [sys.executable, "untracked_command.sh"]
    suite.write_text(json.dumps(payload), encoding="utf-8")
    arguments, _ = _real_candidate(evidence_case, monkeypatch)
    assert evidence.main(arguments, repo_root=repo) == 1
    assert not output.exists()


def test_checkout_eol_rules_preserve_strict_blob_proof(
    evidence_case: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, suite, output = evidence_case
    # Only ordinary fixture data; built-in text/eol normalization, no filters.
    # Reproduce the previous automatic EOL policy, then restore exact LF bytes.
    (repo / ".gitattributes").write_bytes(b"* text=auto\n")
    for relative in ("baseline.md", "harness.py", "lock.txt", "input.json", "probe.py", "suite.json"):
        path = repo / relative
        path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))
    input_path = repo / "input.json"
    input_path.write_bytes(b'{"expected": "observed"}\n')
    arguments, head = _real_candidate(evidence_case, monkeypatch)
    _temporary_git(repo, "config", "core.autocrlf", "true")
    original = input_path.read_bytes()
    assert b"\r\n" not in original and original.endswith(b"\n")
    input_path.write_bytes(original.replace(b"\n", b"\r\n"))
    # Git's EOL-aware cleanliness can vary by platform/configuration. The exact
    # committed-blob check must independently reject this byte mismatch.
    definition, digests = evidence.load_suite(suite, repo)
    with pytest.raises(evidence.EvidenceError, match="working content"):
        evidence.validate_checkout_inputs(repo, head, definition, digests)
    assert evidence.main(arguments, repo_root=repo) == 1
    assert not output.exists()
    input_path.write_bytes(original)
    assert evidence.git_identity(repo)["tracked_worktree_clean"] is True
    assert evidence.main(arguments, repo_root=repo) == 0


@pytest.mark.parametrize("suffix", [".py", ".pyd", ".so", ".pth"])
def test_ignored_cache_cannot_hide_source_or_executable_modules(
    evidence_case: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch, suffix: str,
) -> None:
    repo, _, output = evidence_case
    (repo / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    cache = repo / "__pycache__"
    cache.mkdir()
    (cache / f"ordinary{suffix}").write_text("# Never imported, harmless fixture\n", encoding="utf-8")
    arguments, _ = _real_candidate(evidence_case, monkeypatch)
    assert evidence.main(arguments, repo_root=repo) == 1
    assert not output.exists()
