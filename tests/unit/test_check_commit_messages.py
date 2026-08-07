"""Unit tests for ``scripts/check_commit_messages.py`` — the commit-message gate (#444).

Two fixture families, matching the script's two failure policies:

- a synthetic STANDARD in ``tmp_path`` exercises the *parsers* (structure in, rules out),
  so a real-tree edit to §4 can never silently flip a parser test green;
- a throwaway git repo in ``tmp_path`` exercises *range collection and exit codes*, per
  ``tests/AGENTS.md`` ("Scripts under test take an injectable repo root ... so fixtures run
  against ``tmp_path``, not the live tree").

Two real-tree pins at the end assert the committed STANDARD still yields the counts the gate
was designed against (35 scopes / 7 types / 23 aliases) and that all three §4.3 forbidden
classes are still diagnosable — those are the numbers #443 established and #444 relies on.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from scripts.check_commit_messages import (
    STANDARD_REL,
    Commit,
    Rules,
    check_commit,
    collect_range,
    load_rules,
    parse_alias_map,
    parse_forbidden_examples,
    parse_scope_whitelist,
    parse_type_whitelist,
    run,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

# A miniature STANDARD carrying every structure the parsers key on: a §3.1 type table, two §4
# scope tables, a §4.3 bullet list (two forbidding bullets + one that must NOT be harvested),
# a §4.6 alias table with a multi-alias row, and a §5 table that must stay out of scope.
FIXTURE_STANDARD = """---
type: standard
---

# Fixture commit convention

## 3 类型（type）

### 3.1 类型定义

| 类型 | 含义 | 何时使用 |
|------|------|---------|
| `feat` | 新功能 | 新增能力 |
| `docs` | 文档变更 | 仅修改文档 |
| `infra` | 基础设施 | CI/CD、脚本 |

## 4 范围（scope）

### 4.1 代码范围（`src/mj_agent/`）

| scope | 覆盖路径 | 示例 header |
|---|---|---|
| `agent` | `agent.py` | `feat(agent): 接入工具` |
| `sql` | `tools/sql/` | `fix(sql): 收紧分号` |

### 4.2.3 兜底（1 项）

| scope | 覆盖路径 | 示例 header |
|---|---|---|
| `infra` | 无更精确 scope 的基础设施面 | `infra(infra): 排除 .worktrees/` |

### 4.3 Scope 约束

- **`docs` 仅作 type 使用，不得作为 scope**。文档改动应取所在区域的 scope（`docs(sdd)`）。*（历史误用 3 次）*
- **不得以 type 作 scope**。`refactor` / `test` 等属 §3 的 type 命名空间。*（历史 25 次）*
- **不得以项目阶段 / 里程碑作 scope**。*（`stage-e` 13 次 + `phase-0.5` 1 次）*
- **一次 commit 只能有一个 scope**。`type(a)(b):` 形式不合规；其 `commit-message.prefix` 已于 `aade0c2` 修正。
- 真正混合无主导 scope 时，省略：`feat: <summary>`

### 4.6 历史别名映射

| 历史写法 | 正式 scope | 说明 |
|---|---|---|
| `plan` | `plans` | 取目录名本身 |
| `skills`、`safe-sql` | `skill` | 一行多别名 |

## 5 分支类型与 Commit 类型

本节的表不得被 scope 解析器收录。

| scope | 覆盖路径 | 示例 header |
|---|---|---|
| `bogus` | 不该出现 | — |
"""


def _write_standard(root: Path, text: str) -> Path:
    path = root / STANDARD_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def fixture_root(tmp_path: Path) -> Path:
    root = tmp_path / "fixture-repo"
    _write_standard(root, FIXTURE_STANDARD)
    return root


@pytest.fixture
def rules(fixture_root: Path) -> Rules:
    return load_rules(fixture_root)


# --------------------------------------------------------------------------
# AC-1 — the rules are DERIVED from the STANDARD, never copied into the script
# --------------------------------------------------------------------------


def test_scope_whitelist_comes_from_scope_headed_tables_only(rules: Rules) -> None:
    assert rules.scopes == {"agent", "sql", "infra"}
    # §4.6's left column holds ILLEGAL historical spellings — including them would let the
    # gate green-light exactly what §4.6 exists to retire.
    assert "plan" not in rules.scopes
    assert "skills" not in rules.scopes
    # §5 is a different section: collection must stop at the `## 5` heading.
    assert "bogus" not in rules.scopes


def test_type_whitelist_comes_from_the_type_table(rules: Rules) -> None:
    assert rules.types == {"feat", "docs", "infra"}


def test_alias_row_may_list_several_aliases(rules: Rules) -> None:
    assert rules.aliases["plan"] == "plans"
    assert rules.aliases["skills"] == "skill"
    assert rules.aliases["safe-sql"] == "skill"


def test_forbidden_examples_only_from_must_not_be_scope_bullets(rules: Rules) -> None:
    # Harvested from the two/three bullets whose bold lead says "…作 scope".
    assert set(rules.forbidden) == {"docs", "refactor", "test", "stage-e", "phase-0.5"}
    # The "one scope per commit" bullet has no such lead; its evidence parenthetical cites a
    # commit SHA and a YAML key that would otherwise be mistaken for forbidden scope names.
    assert "aade0c2" not in rules.forbidden
    assert "commit-message.prefix" not in rules.forbidden
    # `infra` is a type AND a whitelisted scope — it must never be shamed.
    assert "infra" not in rules.forbidden


def test_new_scope_in_the_standard_is_honored_without_touching_the_script(
    fixture_root: Path,
) -> None:
    """AC-1: add a scope to the STANDARD → the gate accepts it, no code change."""
    before = load_rules(fixture_root)
    assert "gateway" not in before.scopes
    assert check_commit(Commit("a" * 40, "feat(gateway): x"), before)[0]

    text = FIXTURE_STANDARD.replace(
        "| `sql` | `tools/sql/` | `fix(sql): 收紧分号` |",
        "| `sql` | `tools/sql/` | `fix(sql): 收紧分号` |\n| `gateway` | `gateway/` | `feat(gateway): x` |",
    )
    _write_standard(fixture_root, text)

    after = load_rules(fixture_root)
    assert "gateway" in after.scopes
    assert check_commit(Commit("a" * 40, "feat(gateway): x"), after) == ([], [])


# --------------------------------------------------------------------------
# AC-2 — fail-closed on unusable verdict inputs (never "cannot parse → pass")
# --------------------------------------------------------------------------


def test_missing_standard_file_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    empty = tmp_path / "no-standard"
    empty.mkdir()
    assert run(["main", "HEAD"], repo_root=empty) == 2
    assert "cannot read the commit STANDARD" in capsys.readouterr().err


def test_missing_scope_section_exits_2(
    fixture_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """§4 renamed / removed → 0 scopes → refuse to run (not "everything is a violation")."""
    text = FIXTURE_STANDARD.replace("## 4 范围（scope）", "## 4444 范围（已改名）")
    _write_standard(fixture_root, text)
    assert run(["main", "HEAD"], repo_root=fixture_root) == 2
    assert "parsed 0 scopes" in capsys.readouterr().err


def test_restructured_scope_table_exits_2(
    fixture_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Header cell `scope` → `范围`: the table is no longer identifiable → fail closed."""
    text = FIXTURE_STANDARD.replace("| scope | 覆盖路径 | 示例 header |", "| 范围 | 覆盖路径 | 示例 |")
    _write_standard(fixture_root, text)
    assert run(["main", "HEAD"], repo_root=fixture_root) == 2
    assert "parsed 0 scopes" in capsys.readouterr().err


def test_restructured_type_table_exits_2(
    fixture_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    text = FIXTURE_STANDARD.replace("| 类型 | 含义 | 何时使用 |", "| type | 含义 | 何时使用 |")
    _write_standard(fixture_root, text)
    assert run(["main", "HEAD"], repo_root=fixture_root) == 2
    assert "parsed 0 types" in capsys.readouterr().err


def test_diagnostics_degrade_but_do_not_fail_closed(fixture_root: Path) -> None:
    """§4.3 / §4.6 reworded → hints vanish, verdicts unchanged.

    Fail-closed guards what DECIDES (whitelist, type list). Making it guard the prose that
    only enriches messages would let a wording edit take the gate down.
    """
    text = FIXTURE_STANDARD.replace("### 4.3 Scope 约束", "### 4.3 约束").replace(
        "| 历史写法 | 正式 scope | 说明 |", "| 旧写法 | 新写法 | 说明 |"
    )
    # Also neutralise the bullets' bold leads so nothing is harvested.
    text = text.replace("不得以 type 作 scope", "不建议这样写").replace(
        "`docs` 仅作 type 使用，不得作为 scope", "`docs` 只是 type"
    )
    _write_standard(fixture_root, text)

    degraded = load_rules(fixture_root)
    assert degraded.scopes == {"agent", "sql", "infra"}
    assert degraded.aliases == {}
    assert "refactor" not in degraded.forbidden

    violations, _ = check_commit(Commit("b" * 40, "docs(plan): x"), degraded)
    assert [v.rule for v in violations] == ["unknown-scope"]
    assert "§4.6" not in violations[0].message  # hint gone, verdict identical


# --------------------------------------------------------------------------
# AC-7 — per-commit checking
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "subject",
    [
        "feat(agent): 接入 describe_biz_table",
        "docs: 更新 README",  # scope omitted — legal per §4.4
        "infra(infra): .gitignore 排除 .worktrees/",
        "feat(agent)!: breaking change marker is Conventional Commits 1.0.0",
        "feat(agent):无空格也不在本期判定面内",
    ],
)
def test_conforming_subjects_produce_no_findings(subject: str, rules: Rules) -> None:
    assert check_commit(Commit("c" * 40, subject), rules) == ([], [])


def test_unknown_scope_is_a_violation(rules: Rules) -> None:
    violations, warnings = check_commit(Commit("d" * 40, "feat(nope): x"), rules)
    assert warnings == []
    assert [v.rule for v in violations] == ["unknown-scope"]
    assert "3 项闭合白名单" in violations[0].message


def test_alias_scope_is_a_violation_with_the_formal_scope_named(rules: Rules) -> None:
    """§4.6 aliases diagnose, they do not green-light (#444 comment ②)."""
    violations, _ = check_commit(Commit("e" * 40, "docs(plan): x"), rules)
    assert [v.rule for v in violations] == ["unknown-scope"]
    assert "正式 scope 为 plans" in violations[0].message
    assert "§4.6" in violations[0].message


def test_type_as_scope_reports_the_specific_rule(rules: Rules) -> None:
    violations, _ = check_commit(Commit("f" * 40, "docs(refactor): x"), rules)
    assert [v.rule for v in violations] == ["unknown-scope"]
    assert "不得以 type 作 scope" in violations[0].message


def test_stage_as_scope_reports_the_specific_rule(rules: Rules) -> None:
    violations, _ = check_commit(Commit("0" * 40, "docs(stage-e): x"), rules)
    assert "不得以项目阶段" in violations[0].message


def test_docs_as_scope_reports_the_specific_rule(rules: Rules) -> None:
    violations, _ = check_commit(Commit("1" * 40, "docs(docs): x"), rules)
    assert "仅作 type 使用" in violations[0].message


def test_unknown_type_is_a_violation(rules: Rules) -> None:
    violations, _ = check_commit(Commit("2" * 40, "maintain(agent): x"), rules)
    assert [v.rule for v in violations] == ["unknown-type"]


def test_uppercase_type_hints_at_the_lowercase_form(rules: Rules) -> None:
    violations, _ = check_commit(Commit("3" * 40, "Feat(agent): x"), rules)
    assert [v.rule for v in violations] == ["unknown-type"]
    assert "应为 `feat`" in violations[0].message


def test_double_paren_scope_is_reported_as_multiple_scopes(rules: Rules) -> None:
    violations, _ = check_commit(Commit("4" * 40, "infra(infra)(deps): bump x"), rules)
    assert [v.rule for v in violations] == ["multiple-scopes"]
    assert "(infra)(deps)" in violations[0].message


def test_empty_scope_parens_are_reported(rules: Rules) -> None:
    violations, _ = check_commit(Commit("5" * 40, "feat(): x"), rules)
    assert [v.rule for v in violations] == ["empty-scope"]


def test_unparseable_header_is_reported(rules: Rules) -> None:
    violations, _ = check_commit(Commit("6" * 40, "Initial commit: mj-agent scaffold"), rules)
    assert [v.rule for v in violations] == ["header-format"]


def test_fixup_is_a_warning_counted_separately(rules: Rules) -> None:
    """#444: `fixup!` reports as a warning, kept apart from scope violations."""
    violations, warnings = check_commit(Commit("7" * 40, "fixup! feat(agent): x"), rules)
    assert violations == []
    assert [w.rule for w in warnings] == ["autosquash-commit"]


@pytest.mark.parametrize("marker", ["squash", "amend"])
def test_every_git_autosquash_marker_lands_in_the_warning_bucket(
    marker: str, rules: Rules
) -> None:
    """`amend!` (git >= 2.32) belongs with fixup!/squash!, not in header-format."""
    violations, warnings = check_commit(Commit("8" * 40, f"{marker}! feat(agent): x"), rules)
    assert violations == []
    assert [w.rule for w in warnings] == ["autosquash-commit"]


def test_uppercase_scope_is_a_violation_because_the_whitelist_is_lowercase(
    rules: Rules,
) -> None:
    """Case IS judged — as a consequence of deriving from lowercase tables.

    The docs must never claim otherwise (they did in an early draft); this pins the truth.
    """
    violations, _ = check_commit(Commit("9" * 40, "feat(AGENT): x"), rules)
    assert [v.rule for v in violations] == ["unknown-scope"]


def test_headings_inside_code_fences_do_not_end_a_section(fixture_root: Path) -> None:
    """A fenced ``## 5`` must not truncate §4 — the naive-scan bug class from #304."""
    text = FIXTURE_STANDARD.replace(
        "### 4.2.3 兜底（1 项）",
        "```markdown\n## 5 这是代码块里的假标题，不得终止 §4 的收集\n```\n\n### 4.2.3 兜底（1 项）",
    )
    _write_standard(fixture_root, text)
    scopes = parse_scope_whitelist((fixture_root / STANDARD_REL).read_text(encoding="utf-8"))
    # `infra` lives in §4.2.3, i.e. AFTER the fenced fake heading.
    assert scopes == {"agent", "sql", "infra"}


# --------------------------------------------------------------------------
# AC-3 / AC-5 — range collection and exit codes against a real (throwaway) repo
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
def git_repo(tmp_path: Path) -> Path:
    """main -> topic with two topic commits, one main-side commit, and a merge commit."""
    repo = tmp_path / "git-repo"
    _write_standard(repo, FIXTURE_STANDARD)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "infra(infra): seed fixture standard")

    _git(repo, "checkout", "-q", "-b", "topic")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "feat(agent): topic one")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "docs(plan): topic two")

    _git(repo, "checkout", "-q", "main")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "docs(refactor): base-side noise")

    _git(repo, "checkout", "-q", "topic")
    _git(repo, "merge", "-q", "--no-ff", "-m", "merge: bring main in", "main")
    return repo


def test_merge_commits_and_base_side_commits_are_excluded(git_repo: Path) -> None:
    """AC-3: the gate sees the PR's OWN non-merge commits and nothing else."""
    subjects = [c.subject for c in collect_range(git_repo, "main", "topic")]
    assert subjects == ["docs(plan): topic two", "feat(agent): topic one"]
    assert "merge: bring main in" not in subjects
    # The base-side commit is a violation, yet must not colour this PR's result.
    assert "docs(refactor): base-side noise" not in subjects


def test_run_returns_1_and_names_the_offender(
    git_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-5: a violation must make the script exit non-zero, or continue-on-error is theatre."""
    assert run(["main", "topic"], repo_root=git_repo) == 1
    captured = capsys.readouterr()
    assert "docs(plan): topic two" in captured.out
    assert json.loads(captured.err)["violations"] == 1


def test_run_returns_0_on_a_clean_range(
    git_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _git(git_repo, "checkout", "-q", "-b", "clean", "main")
    _git(git_repo, "commit", "-q", "--allow-empty", "-m", "feat(agent): entirely conforming")
    assert run(["main", "clean"], repo_root=git_repo) == 0
    assert "OK: 1 commit(s)" in capsys.readouterr().out


def test_unresolvable_range_fails_closed(
    git_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An input the gate cannot read must not read as "nothing wrong" (#429's lesson)."""
    assert run(["no-such-ref", "topic"], repo_root=git_repo) == 2
    assert "GATE ERROR" in capsys.readouterr().err


def test_resolvable_but_empty_range_is_not_an_error(
    git_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Empty is valid input; only UNREADABLE input is the fail-closed case."""
    assert run(["main", "main"], repo_root=git_repo) == 0
    assert "0 non-merge commits in range" in capsys.readouterr().out


def test_dry_run_suppresses_the_exit_code(
    git_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(["--dry-run", "-n", "50", "topic"], repo_root=git_repo) == 0
    out = capsys.readouterr().out
    assert "DRY-RUN" in out
    assert "FAIL:" in out  # it still reports; it just does not gate


# --------------------------------------------------------------------------
# Real-tree pins — the committed STANDARD still yields what the gate expects
# --------------------------------------------------------------------------


def test_real_standard_yields_the_counts_443_established() -> None:
    text = (REPO_ROOT / STANDARD_REL).read_text(encoding="utf-8")
    scopes = parse_scope_whitelist(text)
    assert len(scopes) == 35, sorted(scopes)
    assert len(parse_type_whitelist(text)) == 7
    assert len(parse_alias_map(text)) == 23


def test_real_standard_keeps_all_three_forbidden_classes_diagnosable() -> None:
    text = (REPO_ROOT / STANDARD_REL).read_text(encoding="utf-8")
    forbidden = parse_forbidden_examples(text, parse_scope_whitelist(text))
    assert "docs" in forbidden  # §4.3 bullet 1
    assert "refactor" in forbidden  # §4.3 bullet 2 (25 historical uses, the single worst)
    assert "stage-e" in forbidden  # §4.3 bullet 3
    assert "infra" not in forbidden  # whitelisted scope that is also a type
