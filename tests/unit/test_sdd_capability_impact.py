"""Unit tests for check_capability_impact reporter (cross-capability-change.md Step 1).

Per the maintain/capability-impact-script plan:

- 3 mapping sources: capabilities/ direct prefix, cross_capability_refs[].surface
  first-path-token (spec.yml + trace.yml; records BOTH sides with a coupling-edge
  label), trace.yml links[].tests[] (::test-id stripped → declaring capability).
- unmapped is WARN (designed-in answer, not an error); exit 1 only under --strict.
- Hard requirement: posix normalization — Windows backslash input must map.
- #217 anti-regression: every main() call injects repo_root=tmp_path; the real
  tree is never touched.

Synthetic-mini-repo fixture style mirrors test_sdd_g8_evidence_required.py.
"""

from __future__ import annotations

import io
from pathlib import Path
from textwrap import dedent

import pytest
from scripts.sdd.check_capability_impact import (
    CouplingEdge,
    _first_path_token,
    build_path_index,
    classify,
    main,
    normalize_path,
)

_ALPHA_SPEC = dedent(
    """\
    id: data-agent.alpha
    name: Alpha
    cross_capability_refs:
      - target: data-agent.beta
        reason: "alpha reads beta's shared helper"
        surface: src/pkg/shared.py:10-20 (helper)
    """
)

_ALPHA_TRACE = dedent(
    """\
    capability: data-agent.alpha
    schema_version: "1.2"
    cross_capability_refs:
      - target: data-agent.beta
        direction: outbound
        surface: "src/pkg/shared.py:10-20 (_helper impl)"
    links:
      - req: REQ-001
        tests:
          - tests/unit/test_alpha.py::TestX::test_y
          - tests/unit/test_alpha_plain.py
    """
)

_BETA_SPEC = dedent(
    """\
    id: data-agent.beta
    name: Beta
    """
)


def _setup_mini_repo(tmp_path: Path) -> Path:
    """Two synthetic capabilities: alpha (edge→beta + tests[]) and beta (plain)."""
    alpha = tmp_path / "capabilities" / "data-agent" / "alpha"
    alpha.mkdir(parents=True)
    (alpha / "spec.yml").write_text(_ALPHA_SPEC, encoding="utf-8")
    (alpha / "trace.yml").write_text(_ALPHA_TRACE, encoding="utf-8")

    beta = tmp_path / "capabilities" / "data-agent" / "beta"
    beta.mkdir(parents=True)
    (beta / "spec.yml").write_text(_BETA_SPEC, encoding="utf-8")
    return tmp_path


class TestSurfaceTokenParsing:
    """_first_path_token tolerance over every in-tree surface shape."""

    def test_line_range_suffix_stripped(self) -> None:
        assert _first_path_token("src/pkg/shared.py:10-20") == "src/pkg/shared.py"

    def test_parenthesised_annotation_stripped(self) -> None:
        assert _first_path_token("src/pkg/shared.py:10-20 (helper)") == "src/pkg/shared.py"

    def test_multi_path_takes_first_segment(self) -> None:
        surface = "src/pkg/a.yaml (periods.*.time_column) + src/pkg/b.py:58-59"
        assert _first_path_token(surface) == "src/pkg/a.yaml"

    def test_symbol_suffix_stripped(self) -> None:
        assert _first_path_token("src/pkg/agent.py:ALL_TOOLS + src/pkg/f.py") == "src/pkg/agent.py"

    def test_prose_tail_without_parens(self) -> None:
        surface = ".mcp.json ssh-manager DGX host entry + src/pkg/config.py llm_base_url"
        assert _first_path_token(surface) == ".mcp.json"

    def test_pure_prose_surface_returns_none(self) -> None:
        assert _first_path_token("compose env_file: ../.env injects LLM_PROVIDER") is None

    def test_empty_and_malformed_return_none(self) -> None:
        assert _first_path_token("") is None
        assert _first_path_token("   ") is None
        assert _first_path_token(None) is None
        assert _first_path_token(123) is None
        assert _first_path_token(["src/pkg/a.py"]) is None


class TestNormalizePath:
    def test_backslash_normalized(self) -> None:
        assert normalize_path("src\\pkg\\shared.py") == "src/pkg/shared.py"

    def test_leading_dot_slash_dropped(self) -> None:
        assert normalize_path("./src/pkg/shared.py") == "src/pkg/shared.py"


class TestClassify:
    """Mapping-source coverage against the synthetic mini repo."""

    def test_direct_prefix_hit(self, tmp_path: Path) -> None:
        index = build_path_index(_setup_mini_repo(tmp_path))
        report = classify(["capabilities/data-agent/alpha/contracts/behavior.feature"], index)
        assert report.unmapped == []
        assert report.affected["data-agent.alpha"] == [
            ("capabilities/data-agent/alpha/contracts/behavior.feature", "capabilities/ prefix")
        ]

    def test_surface_hit_records_both_sides_with_coupling_edge_label(
        self, tmp_path: Path
    ) -> None:
        index = build_path_index(_setup_mini_repo(tmp_path))
        report = classify(["src/pkg/shared.py"], index)
        via = "coupling-edge data-agent.alpha→data-agent.beta"
        assert report.affected["data-agent.alpha"] == [("src/pkg/shared.py", via)]
        assert report.affected["data-agent.beta"] == [("src/pkg/shared.py", via)]

    def test_spec_and_trace_same_surface_dedup_to_one_edge(self, tmp_path: Path) -> None:
        index = build_path_index(_setup_mini_repo(tmp_path))
        assert index.surfaces["src/pkg/shared.py"] == {
            CouplingEdge(declaring="data-agent.alpha", target="data-agent.beta")
        }

    def test_trace_tests_hit_strips_test_id(self, tmp_path: Path) -> None:
        index = build_path_index(_setup_mini_repo(tmp_path))
        report = classify(["tests/unit/test_alpha.py"], index)
        assert report.affected["data-agent.alpha"] == [
            ("tests/unit/test_alpha.py", "trace.yml links[].tests[]")
        ]

    def test_unmapped_collected(self, tmp_path: Path) -> None:
        index = build_path_index(_setup_mini_repo(tmp_path))
        report = classify(["README.md"], index)
        assert report.affected == {}
        assert report.unmapped == ["README.md"]

    def test_backslash_input_normalized(self, tmp_path: Path) -> None:
        index = build_path_index(_setup_mini_repo(tmp_path))
        report = classify(["src\\pkg\\shared.py"], index)
        assert "data-agent.alpha" in report.affected
        assert report.unmapped == []

    def test_input_deduplicated(self, tmp_path: Path) -> None:
        index = build_path_index(_setup_mini_repo(tmp_path))
        report = classify(["src/pkg/shared.py", "src\\pkg\\shared.py", "src/pkg/shared.py"], index)
        assert report.files == ["src/pkg/shared.py"]
        assert len(report.affected["data-agent.alpha"]) == 1


class TestShapeTolerance:
    """字段缺失/类型异常 → skip + WARN，不抛栈."""

    def test_refs_not_a_list_warns_without_raising(self, tmp_path: Path) -> None:
        cap = tmp_path / "capabilities" / "data-agent" / "gamma"
        cap.mkdir(parents=True)
        (cap / "spec.yml").write_text(
            "id: data-agent.gamma\ncross_capability_refs: not-a-list\n", encoding="utf-8"
        )
        index = build_path_index(tmp_path)
        assert any("cross_capability_refs is str" in w for w in index.warnings)

    def test_ref_entry_missing_surface_warns(self, tmp_path: Path) -> None:
        cap = tmp_path / "capabilities" / "data-agent" / "gamma"
        cap.mkdir(parents=True)
        (cap / "spec.yml").write_text(
            dedent(
                """\
                id: data-agent.gamma
                cross_capability_refs:
                  - target: data-agent.alpha
                """
            ),
            encoding="utf-8",
        )
        index = build_path_index(tmp_path)
        assert any("surface missing/empty" in w for w in index.warnings)
        assert index.surfaces == {}

    def test_unparseable_spec_warns_and_falls_back_to_dir_id(self, tmp_path: Path) -> None:
        cap = tmp_path / "capabilities" / "data-agent" / "gamma"
        cap.mkdir(parents=True)
        (cap / "spec.yml").write_text("id: [unclosed\n", encoding="utf-8")
        index = build_path_index(tmp_path)
        assert any("parse failed" in w for w in index.warnings)
        assert index.prefixes["capabilities/data-agent/gamma/"] == "data-agent.gamma"


class TestMain:
    """CLI behaviour; repo_root always injected (#217 anti-regression)."""

    def test_mapped_and_unmapped_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _setup_mini_repo(tmp_path)
        rc = main(["src/pkg/shared.py", "README.md"], repo_root=root)
        out = capsys.readouterr().out
        assert rc == 0
        assert "[PASS] data-agent.alpha: src/pkg/shared.py" in out
        assert "[PASS] data-agent.beta: src/pkg/shared.py" in out
        assert "coupling-edge data-agent.alpha→data-agent.beta" in out
        assert "[WARN] unmapped: README.md" in out
        assert "/mj-agent-flow-scope-drift" in out
        assert "2 capability(ies) affected / 1 unmapped (over 2 files)" in out

    def test_strict_exit_1_on_unmapped(self, tmp_path: Path) -> None:
        root = _setup_mini_repo(tmp_path)
        assert main(["README.md"], repo_root=root) == 0
        assert main(["README.md", "--strict"], repo_root=root) == 1

    def test_strict_exit_0_when_all_mapped(self, tmp_path: Path) -> None:
        root = _setup_mini_repo(tmp_path)
        assert main(["src/pkg/shared.py", "--strict"], repo_root=root) == 0

    def test_stdin_appends_files(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        root = _setup_mini_repo(tmp_path)
        monkeypatch.setattr("sys.stdin", io.StringIO("tests/unit/test_alpha.py\n\n"))
        rc = main(["--stdin", "README.md"], repo_root=root)
        out = capsys.readouterr().out
        assert rc == 0
        assert "[PASS] data-agent.alpha: tests/unit/test_alpha.py" in out
        assert "(over 2 files)" in out

    def test_empty_input_exits_0(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _setup_mini_repo(tmp_path)
        rc = main([], repo_root=root)
        out = capsys.readouterr().out
        assert rc == 0
        assert "0 capability(ies) affected / 0 unmapped (over 0 files)" in out

    def test_no_capabilities_dir_graceful(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = main(["src/pkg/shared.py"], repo_root=tmp_path)
        out = capsys.readouterr().out
        assert rc == 0
        assert "no capabilities/ directory" in out
        assert "[WARN] unmapped: src/pkg/shared.py" in out
