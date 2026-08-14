"""Contract: the sanitized-snapshot validator in ``scripts/diff_biz_schema.py``.

Epic #499 PR-0c. Exercises the closed ``schema-v1`` envelope, the sanctioned-root path
confinement, the injectable 7-day freshness clock, and the SKIP semantics — entirely from
synthetic fixtures. No database, no network, no credentials, no wall clock.

The central invariant under test: **a SKIP never masquerades as a PASS.**
"""

from __future__ import annotations

import datetime as dt
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from scripts.diff_biz_schema import (
    EXIT_DRIFT,
    EXIT_OK,
    EXIT_REJECT,
    RESULT_DRIFT,
    RESULT_PASS,
    RESULT_SKIP_NO_SNAPSHOT,
    RESULT_SKIP_STALE,
    SNAPSHOT_ROOT,
    SnapshotRejected,
    load_snapshot,
)
from scripts.diff_biz_schema import main as diff_main

from tests.contract.snapshot_fixtures import (
    FIXTURE_DIR,
    FRESH_NOW,
    STALE_NOW,
    VALID_SNAPSHOT,
    install,
    make_repo_root,
)

pytestmark = pytest.mark.contract


def _make_dir_link(link: Path, target: Path) -> bool:
    """Create a directory link at ``link`` pointing at ``target``. False if unsupported.

    Prefers a Windows junction, which — unlike a symlink — needs no elevated privileges,
    so this exercises the redirected-root branch on an ordinary developer/CI box.
    """
    link.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        proc = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode == 0 and link.exists():
            return True
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        return False
    return True

#: Every negative fixture and the envelope rule it violates.
_REJECTED_FIXTURES = [
    ("missing_field.yaml", "missing required field"),
    ("unknown_field.yaml", "unknown top-level field"),
    ("bad_provenance.yaml", "provenance must be"),
    ("not_sanitized.yaml", "sanitized must be boolean true"),
    ("sanitized_truthy_string.yaml", "sanitized must be boolean true"),
    ("bad_schema_version.yaml", "unsupported schema_version"),
    ("naive_captured_at.yaml", "explicit timezone offset"),
    ("yaml_alias.yaml", "alias"),
    # Both tag fixtures must be refused by OUR allowlist, not incidentally by SafeLoader
    # declining to construct a dangerous python tag — hence the benign-tag twin.
    ("custom_tag.yaml", "explicit YAML tag"),
    ("benign_custom_tag.yaml", "explicit YAML tag"),
    ("payload_not_mapping.yaml", "payload must be a mapping"),
    ("payload_bad_interior.yaml", "columns must be a list"),
]


class TestClosedEnvelope:
    """`schema-v1` is closed: unknown, sensitive, tag and alias inputs are rejected."""

    @pytest.mark.parametrize(
        ("fixture_name", "expected_message"),
        _REJECTED_FIXTURES,
        ids=[name.removesuffix(".yaml") for name, _ in _REJECTED_FIXTURES],
    )
    def test_invalid_snapshot_is_rejected(
        self, fixture_name: str, expected_message: str
    ) -> None:
        path = FIXTURE_DIR / fixture_name
        assert path.exists(), f"negative fixture missing: {path}"
        with pytest.raises(SnapshotRejected) as excinfo:
            load_snapshot(path)
        assert expected_message in str(excinfo.value), (
            f"{fixture_name} was rejected, but for the wrong reason: {excinfo.value}"
        )

    def test_negative_fixture_set_is_not_empty(self) -> None:
        # Guards the parametrize list against silently collapsing to zero cases.
        assert len(_REJECTED_FIXTURES) >= 12

    def test_every_negative_fixture_on_disk_is_exercised(self) -> None:
        """No negative fixture may sit in the directory unreferenced.

        Without this, adding a fixture and forgetting to list it looks like coverage but
        tests nothing.
        """
        on_disk = {p.name for p in FIXTURE_DIR.glob("*.yaml")} - {VALID_SNAPSHOT}
        assert on_disk, "no negative fixtures found on disk"
        referenced = {name for name, _ in _REJECTED_FIXTURES}
        assert on_disk == referenced, (
            f"negative fixtures on disk but not exercised: {sorted(on_disk - referenced)}; "
            f"listed but missing from disk: {sorted(referenced - on_disk)}"
        )

    def test_valid_snapshot_loads(self) -> None:
        captured_at, payload = load_snapshot(FIXTURE_DIR / VALID_SNAPSHOT)
        assert captured_at == dt.datetime(2026, 8, 13, 0, 0, tzinfo=dt.UTC)
        assert payload["schemas"]["biz_dws"]["tables"], "payload lost its biz_dws tables"


class TestSkipSemantics:
    """No snapshot and stale snapshot both exit 0 without ever claiming PASS."""

    def test_no_snapshot_skips(self, tmp_path: Path, capsys) -> None:
        root = make_repo_root(tmp_path)
        rc = diff_main([], repo_root=root, now=FRESH_NOW)
        out = capsys.readouterr().out
        assert rc == EXIT_OK
        assert RESULT_SKIP_NO_SNAPSHOT in out
        assert RESULT_PASS not in out, "SKIP output must never contain the PASS result code"
        assert "NOT a pass" in out

    def test_stale_snapshot_skips(self, tmp_path: Path, capsys) -> None:
        root = make_repo_root(tmp_path)
        install(root, VALID_SNAPSHOT)
        rc = diff_main([], repo_root=root, now=STALE_NOW)
        out = capsys.readouterr().out
        assert rc == EXIT_OK
        assert RESULT_SKIP_STALE in out
        assert RESULT_PASS not in out, "SKIP output must never contain the PASS result code"
        assert "NOT a pass" in out

    def test_boundary_exactly_seven_days_is_not_stale(self, tmp_path: Path, capsys) -> None:
        root = make_repo_root(tmp_path)
        install(root, VALID_SNAPSHOT)
        exactly_seven_days = dt.datetime(2026, 8, 20, 0, 0, tzinfo=dt.UTC)
        rc = diff_main([], repo_root=root, now=exactly_seven_days)
        out = capsys.readouterr().out
        assert rc == EXIT_OK
        assert RESULT_SKIP_STALE not in out
        assert RESULT_PASS in out

    def test_boundary_one_second_past_seven_days_is_stale(
        self, tmp_path: Path, capsys
    ) -> None:
        root = make_repo_root(tmp_path)
        install(root, VALID_SNAPSHOT)
        just_past = dt.datetime(2026, 8, 20, 0, 0, 1, tzinfo=dt.UTC)
        rc = diff_main([], repo_root=root, now=just_past)
        assert rc == EXIT_OK
        assert RESULT_SKIP_STALE in capsys.readouterr().out

    def test_future_capture_is_rejected_not_treated_as_fresh(
        self, tmp_path: Path, capsys
    ) -> None:
        # A snapshot dated in the future would otherwise never go stale.
        root = make_repo_root(tmp_path)
        install(root, VALID_SNAPSHOT)
        long_before = dt.datetime(2026, 1, 1, 0, 0, tzinfo=dt.UTC)
        rc = diff_main([], repo_root=root, now=long_before)
        assert rc == EXIT_REJECT
        assert "future" in capsys.readouterr().err

    def test_clock_skew_boundary_just_inside_is_accepted(self, tmp_path: Path) -> None:
        """Pin SNAPSHOT_MAX_CLOCK_SKEW itself.

        Without a boundary pair, widening the skew constant (say to 180 days) leaves the
        whole suite green while re-opening the never-goes-stale hole.
        """
        root = make_repo_root(tmp_path)
        install(root, VALID_SNAPSHOT)
        # captured 2026-08-13T00:00Z; 59 minutes before it => within the 1h skew allowance
        now = dt.datetime(2026, 8, 12, 23, 1, tzinfo=dt.UTC)
        assert diff_main([], repo_root=root, now=now) == EXIT_OK

    def test_clock_skew_boundary_just_outside_is_rejected(
        self, tmp_path: Path, capsys
    ) -> None:
        root = make_repo_root(tmp_path)
        install(root, VALID_SNAPSHOT)
        # 61 minutes before capture => beyond the 1h skew allowance
        now = dt.datetime(2026, 8, 12, 22, 59, tzinfo=dt.UTC)
        assert diff_main([], repo_root=root, now=now) == EXIT_REJECT
        assert "future" in capsys.readouterr().err


class TestHappyPathAndDrift:
    """A valid, fresh snapshot yields PASS; a mutated one yields DRIFT (exit 1)."""

    def test_valid_fresh_snapshot_passes(self, tmp_path: Path, capsys) -> None:
        root = make_repo_root(tmp_path)
        install(root, VALID_SNAPSHOT)
        rc = diff_main([], repo_root=root, now=FRESH_NOW)
        out = capsys.readouterr().out
        assert rc == EXIT_OK, f"expected PASS, got rc={rc}; out={out}"
        assert RESULT_PASS in out

    def test_missing_signal_table_is_drift(self, tmp_path: Path, capsys) -> None:
        root = make_repo_root(tmp_path)
        target = install(root, VALID_SNAPSHOT)
        text = target.read_text(encoding="utf-8")
        mutated = text.replace("dws_qcm_ready_signal:", "dws_qcm_renamed_signal:")
        assert mutated != text, "mutation did not apply - fixture layout changed"
        target.write_text(mutated, encoding="utf-8")

        rc = diff_main([], repo_root=root, now=FRESH_NOW)
        err = capsys.readouterr().err
        assert rc == EXIT_DRIFT
        assert RESULT_DRIFT in err
        assert "dws_qcm_ready_signal" in err

    def test_snapshot_with_no_fact_tables_is_drift_not_pass(
        self, tmp_path: Path, capsys
    ) -> None:
        """A payload carrying zero QCM fact tables must NOT report PASS.

        The per-table time-column loop derives its subject from the snapshot, so with no
        fact tables it iterates zero times. Catalog-first period coverage is what stops
        that from becoming a vacuous PASS_NO_DRIFT.
        """
        root = make_repo_root(tmp_path)
        target = install(root, VALID_SNAPSHOT)
        text = target.read_text(encoding="utf-8")
        # Drop every *_total fact table, keeping the 3 signal tables and both dim tables.
        mutated = re.sub(
            r"\n        dws_qcm_qrynum_\w+_total:.*?(?=\n        \w|\n    biz_dwd:)",
            "",
            text,
            flags=re.DOTALL,
        )
        assert "dws_qcm_qrynum_daily_total" not in mutated, (
            "mutation did not remove the fact tables - fixture layout changed"
        )
        assert "dws_qcm_ready_signal" in mutated, "mutation over-reached and ate the signals"
        target.write_text(mutated, encoding="utf-8")

        rc = diff_main([], repo_root=root, now=FRESH_NOW)
        out, err = capsys.readouterr()
        assert rc == EXIT_DRIFT, f"expected DRIFT for an empty-fact snapshot, got rc={rc}"
        assert RESULT_PASS not in out
        assert "_total fact table in snapshot for period=" in err

    def test_wrong_period_time_column_is_drift(self, tmp_path: Path, capsys) -> None:
        """A monthly table carrying the *daily* time column must be caught.

        Matching against the union of all periods' time columns would let this pass — the
        exact per-period rename this check exists to detect.
        """
        root = make_repo_root(tmp_path)
        target = install(root, VALID_SNAPSHOT)
        text = target.read_text(encoding="utf-8")
        mutated = text.replace(
            "            - {name: month, type: text, nullable: false, comment: null}",
            "            - {name: data_date, type: date, nullable: false, comment: null}",
        )
        assert mutated != text, "mutation did not apply - fixture layout changed"
        target.write_text(mutated, encoding="utf-8")

        rc = diff_main([], repo_root=root, now=FRESH_NOW)
        err = capsys.readouterr().err
        assert rc == EXIT_DRIFT, "monthly table with a daily time column must be drift"
        assert "dws_qcm_qrynum_monthly_total" in err

    def test_missing_dimension_join_key_is_drift(self, tmp_path: Path, capsys) -> None:
        root = make_repo_root(tmp_path)
        target = install(root, VALID_SNAPSHOT)
        text = target.read_text(encoding="utf-8")
        mutated = text.replace("name: tenant_id", "name: org_id")
        assert mutated != text, "mutation did not apply - fixture layout changed"
        target.write_text(mutated, encoding="utf-8")

        rc = diff_main([], repo_root=root, now=FRESH_NOW)
        err = capsys.readouterr().err
        assert rc == EXIT_DRIFT
        assert "tenant_id" in err


class TestPathConfinement:
    """Explicit snapshot paths must stay inside the sanctioned root."""

    def test_relative_escape_is_rejected(self, tmp_path: Path, capsys) -> None:
        root = make_repo_root(tmp_path)
        shutil.copyfile(FIXTURE_DIR / VALID_SNAPSHOT, root / "outside.yaml")
        rc = diff_main(
            ["--snapshot", "../../outside.yaml"], repo_root=root, now=FRESH_NOW
        )
        assert rc == EXIT_REJECT
        assert "escapes the sanctioned root" in capsys.readouterr().err

    def test_absolute_path_outside_root_is_rejected(self, tmp_path: Path, capsys) -> None:
        root = make_repo_root(tmp_path)
        elsewhere = tmp_path / "elsewhere.yaml"
        shutil.copyfile(FIXTURE_DIR / VALID_SNAPSHOT, elsewhere)
        rc = diff_main(["--snapshot", str(elsewhere)], repo_root=root, now=FRESH_NOW)
        assert rc == EXIT_REJECT
        assert "escapes the sanctioned root" in capsys.readouterr().err

    def test_named_missing_snapshot_is_rejected_not_skipped(
        self, tmp_path: Path, capsys
    ) -> None:
        root = make_repo_root(tmp_path)
        rc = diff_main(["--snapshot", "typo.yaml"], repo_root=root, now=FRESH_NOW)
        assert rc == EXIT_REJECT, "a named-but-absent file is a caller error, not a SKIP"
        assert RESULT_SKIP_NO_SNAPSHOT not in capsys.readouterr().out

    def test_directory_is_not_a_regular_file(self, tmp_path: Path, capsys) -> None:
        root = make_repo_root(tmp_path)
        (root / SNAPSHOT_ROOT / "decoy.yaml").mkdir(parents=True)
        rc = diff_main([], repo_root=root, now=FRESH_NOW)
        assert rc == EXIT_REJECT
        assert "not a regular file" in capsys.readouterr().err

    def test_empty_file_is_rejected(self, tmp_path: Path, capsys) -> None:
        root = make_repo_root(tmp_path)
        (root / SNAPSHOT_ROOT / "empty.yaml").write_text("", encoding="utf-8")
        rc = diff_main([], repo_root=root, now=FRESH_NOW)
        assert rc == EXIT_REJECT
        assert "empty" in capsys.readouterr().err

    def test_oversize_file_is_rejected(self, tmp_path: Path, monkeypatch, capsys) -> None:
        # Shrink the bound rather than writing megabytes of test data.
        monkeypatch.setattr("scripts.diff_biz_schema.SNAPSHOT_MAX_BYTES", 128)
        root = make_repo_root(tmp_path)
        install(root, VALID_SNAPSHOT)
        rc = diff_main([], repo_root=root, now=FRESH_NOW)
        assert rc == EXIT_REJECT
        assert "exceeds" in capsys.readouterr().err

    def test_reparse_point_is_rejected_without_needing_symlink_privileges(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        """Cover the reparse-point branch on hosts that cannot create symlinks.

        Creating a real symlink needs elevated privileges on Windows, so the test below
        skips there. This one forces the detector's verdict instead, proving the branch is
        wired to a rejection rather than leaving it unexercised on the CI host.
        """
        root = make_repo_root(tmp_path)
        install(root, VALID_SNAPSHOT)
        monkeypatch.setattr("scripts.diff_biz_schema._is_reparse_point", lambda _p: True)
        rc = diff_main([], repo_root=root, now=FRESH_NOW)
        assert rc == EXIT_REJECT
        assert "symlink/reparse point" in capsys.readouterr().err

    def test_redirected_snapshot_root_is_rejected(self, tmp_path: Path, capsys) -> None:
        """The sanctioned ROOT itself must be anchored, not just its entries.

        If the root (or its `.mj-agent-local` parent) is a junction/symlink,
        ``root.resolve()`` adopts the redirected target as authoritative and the in-root
        containment check compares escaped-against-escaped, passing trivially — an
        out-of-repo read reported as PASS_NO_DRIFT.
        """
        repo_root = tmp_path / "repo"
        (repo_root / ".mj-agent-local").mkdir(parents=True)
        outside = tmp_path / "outside"
        outside.mkdir()
        shutil.copyfile(FIXTURE_DIR / VALID_SNAPSHOT, outside / "planted.yaml")

        link = repo_root / SNAPSHOT_ROOT
        if not _make_dir_link(link, outside):
            pytest.skip("SKIP_POLICY_EXTERNAL_DEPENDENCY: cannot create a directory link here")
        assert (link / "planted.yaml").exists(), "link did not expose the outside directory"

        rc = diff_main([], repo_root=repo_root, now=FRESH_NOW)
        out, err = capsys.readouterr()
        assert rc == EXIT_REJECT, f"redirected root must fail closed, got rc={rc}; out={out}"
        assert RESULT_PASS not in out
        assert "redirected outside the repo" in err

    def test_redirected_parent_of_snapshot_root_is_rejected(
        self, tmp_path: Path, capsys
    ) -> None:
        """Redirecting `.mj-agent-local` leaves the leaf a plain dir — a leaf-only reparse
        check provably misses this, so the anchor must be on the resolved root path."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir(parents=True)
        outside = tmp_path / "outside"
        (outside / "biz-schema-snapshots").mkdir(parents=True)
        shutil.copyfile(
            FIXTURE_DIR / VALID_SNAPSHOT, outside / "biz-schema-snapshots" / "planted.yaml"
        )

        if not _make_dir_link(repo_root / ".mj-agent-local", outside):
            pytest.skip("SKIP_POLICY_EXTERNAL_DEPENDENCY: cannot create a directory link here")

        rc = diff_main([], repo_root=repo_root, now=FRESH_NOW)
        out, err = capsys.readouterr()
        assert rc == EXIT_REJECT, f"redirected parent must fail closed, got rc={rc}"
        assert RESULT_PASS not in out
        assert "redirected outside the repo" in err

    def test_symlinked_snapshot_is_rejected(self, tmp_path: Path, capsys) -> None:
        root = make_repo_root(tmp_path)
        outside = root / "real_target.yaml"
        shutil.copyfile(FIXTURE_DIR / VALID_SNAPSHOT, outside)
        link = root / SNAPSHOT_ROOT / "link.yaml"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError) as exc:
            pytest.skip(f"SKIP_POLICY_EXTERNAL_DEPENDENCY: cannot create symlink here ({exc})")
        assert stat.S_ISLNK(link.lstat().st_mode), "symlink was not created as a link"

        rc = diff_main([], repo_root=root, now=FRESH_NOW)
        assert rc == EXIT_REJECT
        assert "symlink" in capsys.readouterr().err
