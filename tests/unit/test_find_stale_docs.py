"""Unit tests for ``scripts/find_stale_docs.py`` (#441 — first coverage).

Bands per ``tests/AGENTS.md`` fixture discipline:

- scan-face config pins + pure helpers run against ``tmp_path`` fixtures;
- range collection and exit codes run ``main(argv, repo_root=...)`` against a
  throwaway git repo in ``tmp_path`` — never against the live tree;
- two real-tree pin tests (workflow posture / trigger paths) enumerate their
  target file explicitly so structural moves fail loudly.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml
from scripts.find_stale_docs import (
    WALK_DIRS,
    WALK_FILES,
    git_diff_renames,
    grep_backtick_refs,
    iter_target_files,
    main,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "check-stale-docs.yml"


def _write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# AC-1 / AC-4(b) — scan-face config pins
# --------------------------------------------------------------------------


class TestScanFaceConfig:
    def test_walk_dirs_cover_the_sdd_kernel(self) -> None:
        # AC-1: the M5 refactor moved governance prose into the kernel four;
        # the scan face must include them — and keep the original two.
        assert {"capabilities", "decisions", "policies", "sdd"} <= set(WALK_DIRS)
        assert {"docs", "plans"} <= set(WALK_DIRS)

    def test_walk_files_cover_all_5_root_files(self) -> None:
        # AC-4(b): parity with check_wikilinks.ROOT_FILES (#267 precedent).
        assert {
            "README.md",
            "CONTRIBUTING.md",
            "CHANGELOG.md",
            "GLOSSARY.md",
            "CLAUDE.md",
        } <= set(WALK_FILES)

    def test_agents_md_is_in_the_scan_face(self) -> None:
        # ADR-035 root exception; its path enumerations already went stale
        # once (#416) — exactly the failure mode this gate exists to catch.
        assert "AGENTS.md" in WALK_FILES


# --------------------------------------------------------------------------
# Pure helpers against tmp_path
# --------------------------------------------------------------------------


class TestGrepBacktickRefs:
    def test_backtick_bounded_ref_found_with_line_number(self, tmp_path: Path) -> None:
        doc = _write(tmp_path, "sdd/gates.md", "a\nsee `scripts/tool.py` here\n")
        assert grep_backtick_refs(doc, "scripts/tool.py") == [
            (2, "see `scripts/tool.py` here")
        ]

    def test_unbackticked_path_is_not_matched(self, tmp_path: Path) -> None:
        doc = _write(tmp_path, "docs/a.md", "scripts/tool.py without backticks\n")
        assert grep_backtick_refs(doc, "scripts/tool.py") == []

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert grep_backtick_refs(tmp_path / "absent.md", "x") == []


class TestIterTargetFiles:
    def test_kernel_dir_md_files_are_walked(self, tmp_path: Path) -> None:
        _write(tmp_path, "sdd/gates.md", "x")
        _write(tmp_path, "policies/ci-gates.md", "x")
        _write(tmp_path, "capabilities/data-agent/README.md", "x")
        _write(tmp_path, "decisions/ADR-001_X.md", "x")
        rels = {p.relative_to(tmp_path).as_posix() for p in iter_target_files(tmp_path)}
        assert {
            "sdd/gates.md",
            "policies/ci-gates.md",
            "capabilities/data-agent/README.md",
            "decisions/ADR-001_X.md",
        } <= rels

    def test_absent_dirs_are_skipped_silently(self, tmp_path: Path) -> None:
        _write(tmp_path, "docs/a.md", "x")
        rels = {p.relative_to(tmp_path).as_posix() for p in iter_target_files(tmp_path)}
        assert rels == {"docs/a.md"}

    def test_non_md_files_in_walk_dirs_are_ignored(self, tmp_path: Path) -> None:
        _write(tmp_path, "sdd/development-agent.yml", "x")
        assert list(iter_target_files(tmp_path)) == []

    def test_all_root_files_are_yielded_when_present(self, tmp_path: Path) -> None:
        for name in WALK_FILES:
            _write(tmp_path, name, "x")
        rels = {p.relative_to(tmp_path).as_posix() for p in iter_target_files(tmp_path)}
        assert set(WALK_FILES) <= rels


# --------------------------------------------------------------------------
# AC-3 / AC-4(a,c,d) — range collection and exit codes against a throwaway repo
# --------------------------------------------------------------------------


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        [
            "git",
            "-c",
            "user.name=fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


@pytest.fixture
def stale_repo(tmp_path: Path) -> Path:
    """base -> topic where topic renames one file and deletes another, both
    backtick-referenced from a kernel doc, a docs/ doc, and AGENTS.md."""
    repo = tmp_path / "stale-repo"
    _write(repo, "scripts/tool.py", "print('x')\n" * 5)
    _write(repo, "scripts/gone.py", "print('y')\n" * 5)
    _write(repo, "sdd/gates.md", "row cites `scripts/tool.py` and `scripts/gone.py`\n")
    _write(repo, "docs/guide.md", "run `scripts/tool.py`\n")
    _write(repo, "AGENTS.md", "generated by `scripts/gone.py`\n")
    _git(repo, "init", "-q", "-b", "base")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed")
    _git(repo, "checkout", "-q", "-b", "topic")
    _git(repo, "mv", "scripts/tool.py", "scripts/tool_v2.py")
    _git(repo, "rm", "-q", "scripts/gone.py")
    _git(repo, "commit", "-q", "-m", "rename one, delete one")
    return repo


class TestGitDiffRenames:
    def test_rename_and_delete_are_both_collected(self, stale_repo: Path) -> None:
        renames = git_diff_renames("base", "topic", stale_repo)
        assert ("scripts/tool.py", "scripts/tool_v2.py") in renames
        assert ("scripts/gone.py", None) in renames

    def test_unresolvable_ref_yields_no_renames(self, stale_repo: Path) -> None:
        assert git_diff_renames("no-such-ref", "topic", stale_repo) == []


class TestMain:
    def test_kernel_and_root_stale_refs_are_detected(
        self, stale_repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # AC-4(a): before #441 the sdd/ and AGENTS.md hits were invisible
        # (the scan face stopped at docs+plans and 3 root files).
        rc = main(["base", "topic"], repo_root=stale_repo)
        out = capsys.readouterr().out
        assert rc == 0
        assert "sdd/gates.md:1" in out
        assert "docs/guide.md:1" in out
        assert "AGENTS.md:1" in out

    def test_exit_code_stays_zero_with_findings(
        self, stale_repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # AC-4(d): warning posture — findings must NOT flip the exit code.
        # Changing this is a ci-blocking-gate-toggle (sdd/gates.md §2 records
        # warning as the long-term stance; #440) and must not land silently.
        rc = main(["base", "topic"], repo_root=stale_repo)
        assert rc == 0
        assert "::warning::" in capsys.readouterr().out

    def test_no_rename_takes_the_ok_short_path(
        self, stale_repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # AC-4(c)
        rc = main(["base", "base"], repo_root=stale_repo)
        assert rc == 0
        assert capsys.readouterr().out.startswith("OK: no rename")

    def test_delete_is_reported_as_deleted(
        self, stale_repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        main(["base", "topic"], repo_root=stale_repo)
        assert "(deleted)" in capsys.readouterr().out

    def test_json_summary_lands_on_stderr(
        self, stale_repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        main(["base", "topic"], repo_root=stale_repo)
        assert '"findings"' in capsys.readouterr().err


# --------------------------------------------------------------------------
# AC-2 / AC-5 — real-tree pins (explicit target file per tests/AGENTS.md)
# --------------------------------------------------------------------------


class TestWorkflowPins:
    @staticmethod
    def _load_workflow() -> dict:
        return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))

    def test_posture_is_still_warning_at_the_step_layer(self) -> None:
        # AC-5: `continue-on-error: true` sits at the STEP layer — the
        # gates.md §2 row makes the step-vs-job distinction load-bearing.
        # Structural assert: a comment-only survival or a silent move to the
        # job layer (which would also mask checkout/setup failures) must fail.
        job = self._load_workflow()["jobs"]["check-stale-docs"]
        assert job["steps"][-1]["continue-on-error"] is True
        assert "continue-on-error" not in job

    def test_trigger_paths_cover_kernel_and_rename_source_faces(self) -> None:
        # AC-2 kernel four + the #441 issue-comment faces (scripts/, .github/)
        # + the root files added to the scan face. Parsed, not substring —
        # a commented-out entry must fail here (#442 regression class).
        wf = self._load_workflow()
        on = wf.get("on") or wf[True]  # YAML 1.1 parses a bare `on:` key as True
        paths = set(on["pull_request"]["paths"])
        assert {
            "capabilities/**",
            "decisions/**",
            "policies/**",
            "sdd/**",
            "scripts/**",
            ".github/**",
            "CONTRIBUTING.md",
            "GLOSSARY.md",
            "AGENTS.md",
        } <= paths, f"missing trigger path(s): live set = {sorted(paths)}"
