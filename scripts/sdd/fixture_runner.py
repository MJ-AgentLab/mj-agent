"""fixture_runner.py — dual-agent-compat P2 fixture harness runner (§12 surface).

Drives one fixture run for one tool (Claude Code or Codex) against one scenario
under `tests/fixtures/development-agent/scenarios/`:

    setup     build an isolated run dir: clean clone + fixture-base commit +
              base/ overlay + optional pre-applied input.patch + rendered prompt
    verify    recompute facts (changed paths / snapshot / command exits), judge
              the agent-written result.json via fixture_comparators.evaluate,
              write verdict.json
    report    aggregate verdict.json files under a runs root
    teardown  remove a run dir (refuses without its setup.json marker)

Contract highlights (program plan §12 + plans/[PLAN]_dual-agent-compat_p2.md §4):
- the fixture-base commit is created HERE in the temp clone (fixed author/date;
  never referencing a developer branch by name for content);
- the agent under test never commits and never creates branches (Gate 5 #3);
- result.json is written OUTSIDE the clone (Gate 5 #1) at RESULT_PATH injected
  into the rendered prompt — expectations themselves are never generated at
  runtime, only absolute paths are substituted;
- `<fixture-base>` placeholders in verification commands are substituted with
  the context.json `fixture_base` ref at EXECUTION time only (the reported
  command strings keep the placeholder for sorted-array comparison).

Exit codes: 0 OK / 1 verdict FAIL / 2 usage or fatal environment error.
`main(argv=None, repo_root=None)` — repo_root injectable for tests (#217).
Read-only towards the live tree; all writes land under the runs root.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

_SCRIPT_NAME = "fixture_runner.py"
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd import fixture_comparators as fc  # noqa: E402
from scripts.sdd.fixture_comparators import (  # noqa: E402
    evaluate,
    git_changed_paths,
    git_working_tree_patch,
    scrubbed_git_env,
    snapshot_workspace,
)

FIXTURES_RELPATH = Path("tests/fixtures/development-agent/scenarios")
SCENARIO_IDS = ("S1", "S2", "S3", "S4", "S5", "S6")
TOOLS = ("claude", "codex")
INPUT_PATCH_ROLES = ("pre-applied", "expected-diff")
FIXTURE_BASE_PLACEHOLDER = "<fixture-base>"

# Deterministic committer identity for the fixture-base commit (§12: the runner
# creates the base commit itself; determinism keeps reruns byte-comparable).
_GIT_IDENTITY_ENV = {
    "GIT_AUTHOR_NAME": "mj-agent-fixture-runner",
    "GIT_AUTHOR_EMAIL": "fixture-runner@mj-agent.invalid",
    "GIT_AUTHOR_DATE": "2026-01-01T00:00:00 +0000",
    "GIT_COMMITTER_NAME": "mj-agent-fixture-runner",
    "GIT_COMMITTER_EMAIL": "fixture-runner@mj-agent.invalid",
    "GIT_COMMITTER_DATE": "2026-01-01T00:00:00 +0000",
}

_PROMPT_ADDENDUM = """
---

## Runner addendum (injected by fixture_runner; not part of the task itself)

- CLONE_PATH: {clone_path}
- RESULT_PATH: {result_path}

Work inside CLONE_PATH as the repository root. When you finish (or stop at a
required approval), write the unified result.json to RESULT_PATH — it is
OUTSIDE the repository work tree on purpose; do not create it inside the clone.
"""

_COMMAND_TIMEOUT_SECONDS = 1800


class FatalRunnerError(Exception):
    """Environment/usage problem — exit 2, never a silent pass."""


def _fail(message: str) -> None:
    print(f"{_SCRIPT_NAME}: {message}", file=sys.stderr)


def _run_git(args: list[str], cwd: Path, *, env_extra: dict[str, str] | None = None) -> str:
    # Scrubbed env: user/system gitconfig must not influence clone/commit/diff
    # (commit.gpgsign, hooksPath, diff.*, core.abbrev, ...) or determinism breaks.
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        env=scrubbed_git_env(env_extra),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise FatalRunnerError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def _load_scenario(fixtures_root: Path, scenario: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    scenario_dir = fixtures_root / scenario
    context_path = scenario_dir / "context.json"
    expected_path = scenario_dir / "expected.yml"
    if not context_path.is_file() or not expected_path.is_file():
        raise FatalRunnerError(f"scenario '{scenario}' incomplete under {fixtures_root}")
    context = json.loads(context_path.read_text(encoding="utf-8"))
    expected = yaml.safe_load(expected_path.read_text(encoding="utf-8"))
    if context.get("scenario_id") != scenario or expected.get("scenario_id") != scenario:
        raise FatalRunnerError(f"scenario_id mismatch inside fixture '{scenario}'")
    role = context.get("input_patch_role")
    if role is not None and role not in INPUT_PATCH_ROLES:
        raise FatalRunnerError(f"unknown input_patch_role '{role}' in {context_path}")
    return scenario_dir, context, expected


def _copy_overlay(base_dir: Path, clone: Path) -> list[str]:
    copied: list[str] = []
    if not base_dir.is_dir():
        return copied
    for src in sorted(base_dir.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(base_dir)
        dest = clone / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        # LF-normalize overlay text so run trees are byte-stable across platforms.
        dest.write_bytes(src.read_bytes().replace(b"\r\n", b"\n"))
        copied.append(rel.as_posix())
    return copied


def _substituted(command: str, fixture_base: str) -> str:
    return command.replace(FIXTURE_BASE_PLACEHOLDER, fixture_base)


def _execute_commands(
    commands: list[str], clone: Path, fixture_base: str, *, log_lines: list[str] | None = None
) -> dict[str, int]:
    exits: dict[str, int] = {}
    for command in commands:
        argv = shlex.split(_substituted(command, fixture_base))
        try:
            proc = subprocess.run(
                argv, cwd=str(clone), capture_output=True, timeout=_COMMAND_TIMEOUT_SECONDS
            )
            exits[command] = proc.returncode
            if log_lines is not None:
                out = proc.stdout.decode("utf-8", "replace")
                err = proc.stderr.decode("utf-8", "replace")
                log_lines.append(
                    f"$ {command}\n[exit {proc.returncode}]\n"
                    f"--- stdout ---\n{out}\n--- stderr ---\n{err}\n"
                )
        except FileNotFoundError:
            exits[command] = 127
            if log_lines is not None:
                log_lines.append(f"$ {command}\n[exit 127: executable not found]\n")
        except subprocess.TimeoutExpired:
            exits[command] = 124
            if log_lines is not None:
                log_lines.append(f"$ {command}\n[exit 124: timeout]\n")
    return exits


def _cmd_setup(args: argparse.Namespace, repo_root: Path) -> int:
    fixtures_root = args.fixtures_root or (repo_root / FIXTURES_RELPATH)
    scenario_dir, context, _expected = _load_scenario(fixtures_root, args.scenario)

    runs_root: Path = args.runs_root
    run_dir = runs_root / f"{args.tool}-{args.scenario}-run{args.run}"
    if run_dir.exists():
        raise FatalRunnerError(f"run dir already exists: {run_dir} (teardown first)")
    run_dir.mkdir(parents=True)
    try:
        return _setup_body(args, repo_root, fixtures_root, scenario_dir, context, _expected, run_dir)
    except BaseException:
        # A half-built run dir (setup.json not yet written) is a dead-end: `setup`
        # refuses to reuse it and `teardown` refuses to delete it. Remove it so a
        # transient failure (uv sync, apply, red-check) is retryable, not manual.
        if not (run_dir / "setup.json").is_file():
            shutil.rmtree(run_dir, ignore_errors=True)
        raise


def _setup_body(
    args: argparse.Namespace,
    repo_root: Path,
    fixtures_root: Path,
    scenario_dir: Path,
    context: dict[str, Any],
    _expected: dict[str, Any],
    run_dir: Path,
) -> int:
    clone = run_dir / "clone"

    # `--git-common-dir` alone returns the RELATIVE string `.git` in a normal
    # (non-worktree) clone, which does not resolve as a clone source from
    # cwd=run_dir; `--path-format=absolute` makes it work in every git layout.
    source = args.source or _run_git(
        ["rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=repo_root
    ).strip()
    _run_git(
        [
            "clone",
            "-c",
            "core.autocrlf=false",
            "--branch",
            args.source_ref,
            str(source),
            str(clone),
        ],
        cwd=run_dir,
    )
    source_sha = _run_git(["rev-parse", "HEAD"], cwd=clone).strip()

    fixture_base = context["fixture_base"]
    _run_git(["switch", "-c", fixture_base], cwd=clone)
    copied = _copy_overlay(scenario_dir / "base", clone)
    if copied:
        _run_git(["add", "-A"], cwd=clone)
        _run_git(
            ["commit", "-m", f"fixture-base: {args.scenario} overlay"],
            cwd=clone,
            env_extra=_GIT_IDENTITY_ENV,
        )
    base_sha = _run_git(["rev-parse", "HEAD"], cwd=clone).strip()

    work_branch = context.get("simulated", {}).get("branch")
    if work_branch:
        _run_git(["switch", "-c", work_branch], cwd=clone)

    if context.get("input_patch_role") == "pre-applied":
        patch = scenario_dir / "input.patch"
        if not patch.is_file():
            raise FatalRunnerError(f"input_patch_role=pre-applied but no input.patch in {scenario_dir}")
        _run_git(["apply", str(patch)], cwd=clone)

    if not args.no_sync:
        proc = subprocess.run(
            ["uv", "sync", "--frozen"], cwd=str(clone), capture_output=True, text=True
        )
        if proc.returncode != 0:
            raise FatalRunnerError(f"uv sync --frozen failed in clone: {proc.stderr.strip()[-500:]}")

    red_exit: int | None = None
    red_node = _expected.get("red_green_node")
    if red_node and not args.no_sync:
        red_exit = _execute_commands([red_node], clone, fixture_base)[red_node]
        if red_exit == 0:
            raise FatalRunnerError(
                "red check failed: expected test node already passes before implementation"
            )

    pre_snapshot = snapshot_workspace(clone)

    request = (scenario_dir / "request.md").read_text(encoding="utf-8")
    result_path = run_dir / "result.json"
    prompt = request + _PROMPT_ADDENDUM.format(
        clone_path=str(clone.resolve()), result_path=str(result_path.resolve())
    )
    (run_dir / "prompt.md").write_text(prompt, encoding="utf-8", newline="\n")

    setup_info = {
        "schema_version": 1,
        "scenario_id": args.scenario,
        "tool": args.tool,
        "run": args.run,
        "fixtures_root": str(fixtures_root.resolve()),
        "source": str(source),
        "source_ref": args.source_ref,
        "source_sha": source_sha,
        "fixture_base": fixture_base,
        "base_sha": base_sha,
        "work_branch": work_branch,
        "overlay_files": copied,
        "input_patch_role": context.get("input_patch_role"),
        "red_exit": red_exit,
        "pre_snapshot": pre_snapshot,
        "synced": not args.no_sync,
    }
    (run_dir / "setup.json").write_text(
        json.dumps(setup_info, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    # Forward-slash (POSIX) absolute paths in the printed hints: they work in
    # bash on both platforms, and — critically — the codex `-c` value is a TOML
    # basic string where a Windows backslash path would inject invalid escapes
    # (\f, \c) and corrupt the parse.
    clone_posix = clone.resolve().as_posix()
    run_posix = run_dir.resolve().as_posix()
    prompt_posix = (run_dir / "prompt.md").resolve().as_posix()
    print(f"[setup] run dir ready: {run_dir}")
    print(f"[setup] clone: {clone}")
    print(f"[setup] prompt: {run_dir / 'prompt.md'}")
    print("[setup] invoke (claude):")
    print(
        f'  cd "{clone_posix}" && claude -p "$(cat \'{prompt_posix}\')" '
        f'--permission-mode acceptEdits --add-dir "{run_posix}"'
    )
    print("[setup] invoke (codex, non-interactive; </dev/null in bash):")
    print(
        f'  cd "{clone_posix}" && codex exec '
        f"-c 'sandbox_workspace_write.writable_roots=[\"{run_posix}\"]' "
        f"\"$(cat '{prompt_posix}')\" </dev/null"
    )
    return 0


def _cmd_verify(args: argparse.Namespace, repo_root: Path) -> int:
    run_dir: Path = args.run_dir
    setup_path = run_dir / "setup.json"
    if not setup_path.is_file():
        raise FatalRunnerError(f"not a fixture run dir (no setup.json): {run_dir}")
    setup_info = json.loads(setup_path.read_text(encoding="utf-8"))
    fixtures_root = Path(setup_info["fixtures_root"])
    scenario = setup_info["scenario_id"]
    scenario_dir, context, expected = _load_scenario(fixtures_root, scenario)
    clone = run_dir / "clone"
    result_path = run_dir / "result.json"
    if not result_path.is_file():
        raise FatalRunnerError(f"agent result missing: {result_path}")
    result = json.loads(result_path.read_text(encoding="utf-8"))

    # Facts BEFORE running verification commands, so command side effects can
    # never mask (or fake) an agent write in the no-write comparison.
    recomputed = git_changed_paths(clone)
    post_snapshot = snapshot_workspace(clone)

    # No-commit guarantee (Gate 5 #3): the agent must not commit. If HEAD moved,
    # `git status`/`git diff HEAD` would see a clean tree and hide the agent's
    # work, so path-scope could trivially pass. Catch it up front.
    extra_failures: list[str] = []
    head_sha = _run_git(["rev-parse", "HEAD"], cwd=clone).strip()
    if setup_info.get("base_sha") and head_sha != setup_info["base_sha"]:
        extra_failures.append(
            f"no-commit: clone HEAD moved from base {setup_info['base_sha'][:12]} "
            f"to {head_sha[:12]} — the agent committed (forbidden by protocol)"
        )
    extra_failures.extend(fc.check_pinned_content(clone, expected.get("pinned_content", [])))
    required = [str(p) for p in expected.get("required_changed_paths", [])]
    missing_required = sorted(set(required) - set(recomputed))
    if missing_required:
        extra_failures.append(
            f"required-changed-paths: expected changes not present: {missing_required}"
        )

    fixture_base = context["fixture_base"]
    commands = [str(c) for c in expected.get("verification", [])]
    log_lines: list[str] = []
    command_exits = (
        _execute_commands(commands, clone, fixture_base, log_lines=log_lines)
        if not args.no_commands
        else {}
    )

    green_exit: int | None = None
    red_node = expected.get("red_green_node")
    if red_node and not args.no_commands:
        green_exit = command_exits.get(red_node)
        if green_exit is None:
            green_exit = _execute_commands(
                [red_node], clone, fixture_base, log_lines=log_lines
            )[red_node]

    (run_dir / "commands.log").write_text(
        "".join(log_lines) or "(no verification commands executed)\n",
        encoding="utf-8",
        newline="\n",
    )

    actual_patch: bytes | None = None
    expected_patch: bytes | None = None
    if expected.get("comparator") == "exact-patch-lf":
        actual_patch = git_working_tree_patch(clone)
        expected_patch = (scenario_dir / "input.patch").read_bytes()

    failures = extra_failures + evaluate(
        str(expected.get("comparator")),
        expected=expected,
        result=result,
        recomputed_changed_paths=recomputed,
        command_exits=command_exits,
        pre_snapshot=setup_info.get("pre_snapshot"),
        post_snapshot=post_snapshot,
        actual_patch=actual_patch,
        expected_patch=expected_patch,
        red_exit=setup_info.get("red_exit"),
        green_exit=green_exit,
    )

    verdict = {
        "schema_version": 1,
        "scenario_id": scenario,
        "tool": setup_info["tool"],
        "run": setup_info["run"],
        "pass": not failures,
        "failures": failures,
        "command_exits": command_exits,
        "recomputed_changed_paths": recomputed,
        "pre_snapshot": setup_info.get("pre_snapshot"),
        "post_snapshot": post_snapshot,
        "base_sha": setup_info.get("base_sha"),
        "source_sha": setup_info.get("source_sha"),
    }
    (run_dir / "verdict.json").write_text(
        json.dumps(verdict, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    status = "PASS" if not failures else "FAIL"
    print(f"[verify] {scenario} {setup_info['tool']} run{setup_info['run']}: {status}")
    for failure in failures:
        print(f"  [FAIL] {failure}")
    return 0 if not failures else 1


def _cmd_report(args: argparse.Namespace, repo_root: Path) -> int:
    rows: list[dict[str, Any]] = []
    for verdict_path in sorted(args.runs_root.glob("*/verdict.json")):
        data = json.loads(verdict_path.read_text(encoding="utf-8"))
        rows.append(
            {
                "run_dir": verdict_path.parent.name,
                "scenario_id": data.get("scenario_id"),
                "tool": data.get("tool"),
                "run": data.get("run"),
                "pass": data.get("pass"),
                "failures": len(data.get("failures", [])),
            }
        )
    print(json.dumps({"schema_version": 1, "runs": rows}, indent=2, ensure_ascii=False))
    return 0 if rows and all(r["pass"] for r in rows) else (1 if rows else 2)


def _cmd_teardown(args: argparse.Namespace, repo_root: Path) -> int:
    run_dir: Path = args.run_dir
    if not (run_dir / "setup.json").is_file():
        raise FatalRunnerError(f"refusing to remove non-run dir (no setup.json): {run_dir}")

    def _force_remove(func: Any, path: str, exc: BaseException) -> None:
        # Windows: .git objects are read-only; chmod +w then retry.
        os.chmod(path, stat.S_IWRITE)
        func(path)

    shutil.rmtree(run_dir, onexc=_force_remove)
    print(f"[teardown] removed {run_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_SCRIPT_NAME,
        description="dual-agent-compat P2 fixture harness runner (program plan §12)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_setup = sub.add_parser("setup", help="prepare an isolated run dir for one scenario")
    p_setup.add_argument("--scenario", required=True, choices=SCENARIO_IDS)
    p_setup.add_argument("--tool", required=True, choices=TOOLS)
    p_setup.add_argument("--run", required=True, type=int)
    p_setup.add_argument("--runs-root", required=True, type=Path)
    p_setup.add_argument("--fixtures-root", type=Path, default=None)
    p_setup.add_argument("--source", default=None, help="clone source (default: git common dir)")
    p_setup.add_argument("--source-ref", default="develop")
    p_setup.add_argument(
        "--no-sync", action="store_true", help="skip uv sync + red check (unit tests)"
    )

    p_verify = sub.add_parser("verify", help="judge one run against expected.yml")
    p_verify.add_argument("--run-dir", required=True, type=Path)
    p_verify.add_argument(
        "--no-commands",
        action="store_true",
        help="skip executing verification commands (unit tests)",
    )

    p_report = sub.add_parser("report", help="aggregate verdicts under a runs root")
    p_report.add_argument("--runs-root", required=True, type=Path)

    p_teardown = sub.add_parser("teardown", help="remove one run dir")
    p_teardown.add_argument("--run-dir", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None, repo_root: Path | None = None) -> int:
    root = (repo_root or _REPO_ROOT).resolve()
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:  # argparse exits 2 on usage errors already
        return int(exc.code or 0)
    handlers = {
        "setup": _cmd_setup,
        "verify": _cmd_verify,
        "report": _cmd_report,
        "teardown": _cmd_teardown,
    }
    try:
        return handlers[args.command](args, root)
    except FatalRunnerError as exc:
        _fail(str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
