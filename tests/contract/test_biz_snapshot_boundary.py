"""Contract: the biz snapshot/diff surface carries no direct DB/introspection/credential route.

Closes AC-08 (`biz tests/scripts contain no direct DB/introspection/credential route;
snapshot validation is closed/offline`) for Epic #499 PR-0c.

These are **static** assertions over source text plus one guarded subprocess run. Nothing
here connects to a database, reads ``.env``, or touches the network — and the one test that
does execute a script refuses to do so until the static import check has already proven the
script cannot open a live route (fail-closed ordering, per plan §5.3).
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.contract

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FETCH = _REPO_ROOT / "scripts" / "fetch_biz_schema.py"
_DIFF = _REPO_ROOT / "scripts" / "diff_biz_schema.py"
_CONTRACT_DIR = _REPO_ROOT / "tests" / "contract"
_ALIGNMENT_TESTS = (
    _CONTRACT_DIR / "test_biz_schema_alignment.py",
    _CONTRACT_DIR / "test_qcm_catalog_alignment.py",
)

#: Everything AC-08 must hold closed: both scripts plus EVERY module in the contract band,
#: derived from the directory so a newly added helper cannot slip past the scan.
_AC08_SURFACE: tuple[Path, ...] = (
    _FETCH,
    _DIFF,
    *sorted(p for p in _CONTRACT_DIR.glob("*.py") if p.name != "__init__.py"),
)

# Any of these, imported by a biz snapshot surface, means a live route is reachable.
_FORBIDDEN_IMPORT_PREFIXES = (
    "dotenv",
    "psycopg",
    "psycopg2",
    "asyncpg",
    "sqlalchemy",
    "requests",
    "httpx",
    "aiohttp",
    "urllib.request",
    "socket",
    "mj_agent.tools.sql.introspect",
    "mj_agent.integrations",
)

# The sanctioned snapshot root; `diff_biz_schema.py` must not read outside it.
_SNAPSHOT_ROOT_LITERAL = ".mj-agent-local/biz-schema-snapshots"

# Session fixtures in tests/conftest.py that unconditionally skip an external band. A biz
# contract test depending on one is gating on an external dependency rather than running.
_RESERVED_EXTERNAL_FIXTURES = frozenset({"live_db", "memory_db"})


def _imported_modules(path: Path) -> set[str]:
    """Every absolute module name imported by ``path``, via AST (not regex)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module)
    return found


def _external_fixture_hits(path: Path) -> set[str]:
    """Reserved external fixtures this module actually *depends on*.

    AST-based on purpose: a substring scan for the fixture name also matches prose in a
    docstring explaining that the gate was removed, which is the opposite of a defect.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if name == "usefixtures":
                hits.update(
                    arg.value
                    for arg in node.args
                    if isinstance(arg, ast.Constant) and arg.value in _RESERVED_EXTERNAL_FIXTURES
                )
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            hits.update(
                arg.arg
                for arg in (*node.args.args, *node.args.kwonlyargs)
                if arg.arg in _RESERVED_EXTERNAL_FIXTURES
            )
    return hits


def _forbidden_hits(path: Path) -> set[str]:
    modules = _imported_modules(path)
    # Guard against a vacuous pass: a parse that yields nothing would make every
    # containment check below trivially true.
    assert modules, f"parsed zero imports from {path} — the AST walk is broken, not the file"
    return {
        module
        for module in modules
        for prefix in _FORBIDDEN_IMPORT_PREFIXES
        if module == prefix or module.startswith(prefix + ".")
    }


class TestNoLiveRouteImports:
    """No biz snapshot surface may import a dotenv/DB/network/introspection module."""

    @pytest.mark.parametrize(
        "path", [pytest.param(p, id=p.stem) for p in _AC08_SURFACE], ids=None
    )
    def test_no_forbidden_imports(self, path: Path) -> None:
        assert path.exists(), f"expected surface missing: {path}"
        hits = _forbidden_hits(path)
        assert not hits, (
            f"{path.relative_to(_REPO_ROOT).as_posix()} imports live-route module(s) "
            f"{sorted(hits)}; AC-08 requires the biz snapshot surface to be closed/offline"
        )

    def test_scan_set_covers_the_whole_contract_band(self) -> None:
        """The AC-08 scan set is derived, not hand-listed.

        A hand-listed set silently stops covering anything added later — a new helper in
        this package could import psycopg and every AC-08 test would stay green.
        """
        on_disk = {p for p in _CONTRACT_DIR.glob("*.py") if p.name != "__init__.py"}
        assert on_disk, "globbed zero python modules in tests/contract"
        missing = on_disk - set(_AC08_SURFACE)
        assert not missing, (
            f"contract-band modules not covered by the AC-08 scan: "
            f"{sorted(p.name for p in missing)}"
        )
        assert _FETCH in _AC08_SURFACE and _DIFF in _AC08_SURFACE


class TestFetchTombstone:
    """`fetch_biz_schema.py` is a fail-closed tombstone: exit 2, sanctioned-route guidance."""

    def test_exits_two_with_sanctioned_route_guidance(self) -> None:
        hits = _forbidden_hits(_FETCH)
        if hits:
            pytest.fail(
                f"refusing to execute {_FETCH.name}: it still imports {sorted(hits)}, which "
                "could open a live DB/network route. Tombstone the imports first — this test "
                "is fail-closed by design and must not run a live-capable script."
            )

        proc = subprocess.run(
            [sys.executable, str(_FETCH)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(_REPO_ROOT),
        )
        assert proc.returncode == 2, (
            f"tombstone must exit 2, got {proc.returncode}\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )
        combined = proc.stdout + proc.stderr
        assert "find_biz_context" in combined and "execute_sql" in combined, (
            "tombstone must point at the sanctioned agent tool-chain "
            f"(find_biz_context -> ... -> execute_sql); got: {combined!r}"
        )

    def test_exits_two_regardless_of_arguments(self) -> None:
        hits = _forbidden_hits(_FETCH)
        if hits:
            pytest.fail(
                f"refusing to execute {_FETCH.name}: still imports {sorted(hits)} (see above)"
            )
        proc = subprocess.run(
            [sys.executable, str(_FETCH), "--output", "should-never-be-written.yaml"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(_REPO_ROOT),
        )
        assert proc.returncode == 2, (
            "tombstone must exit 2 for every argv shape, so no caller can coax it into "
            f"producing output; got {proc.returncode}"
        )
        assert not (_REPO_ROOT / "should-never-be-written.yaml").exists(), (
            "tombstone wrote an output file"
        )


class TestDiffReadsOnlySanctionedRoot:
    """`diff_biz_schema.py` may only read snapshots under the gitignored local root."""

    def test_names_the_sanctioned_snapshot_root(self) -> None:
        source = _DIFF.read_text(encoding="utf-8")
        assert _SNAPSHOT_ROOT_LITERAL in source, (
            f"{_DIFF.name} must confine snapshot reads to {_SNAPSHOT_ROOT_LITERAL}/"
        )

    def test_does_not_reference_the_legacy_runbook_snapshot_path(self) -> None:
        source = _DIFF.read_text(encoding="utf-8")
        assert "docs/runbook/biz_schema_snapshot" not in source, (
            f"{_DIFF.name} still references the pre-PR-0c docs/runbook snapshot path"
        )


class TestAlignmentTestsAreFixtureOnly:
    """Neither pre-existing alignment contract test may gate on credentials."""

    @pytest.mark.parametrize(
        "path", [pytest.param(p, id=p.stem) for p in _ALIGNMENT_TESTS]
    )
    def test_no_external_fixture_gate(self, path: Path) -> None:
        hits = _external_fixture_hits(path)
        assert not hits, (
            f"{path.name} still depends on reserved external fixture(s) {sorted(hits)}; "
            "PR-0c requires fixture-only contract tests with no credential gate"
        )

    def test_alignment_test_set_is_not_empty(self) -> None:
        # A collapsed tuple would make every parametrized check above vanish silently.
        assert len(_ALIGNMENT_TESTS) == 2
