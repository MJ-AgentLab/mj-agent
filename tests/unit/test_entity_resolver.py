"""Unit tests for the entity resolver (Phase 1 sub 1.C)."""

from __future__ import annotations

import pytest

from mj_agent.entity import (
    DEFAULT_FUZZY_THRESHOLD,
    EntityKind,
    load_aliases,
    load_codebook,
    resolve,
)
from mj_agent.entity.tools import entity_lookup


@pytest.fixture(autouse=True)
def _clear_caches() -> None:
    load_aliases.cache_clear()
    load_codebook.cache_clear()


class TestL1Exact:
    def test_canonical_full_name(self) -> None:
        r = resolve("上海银行股份有限公司", EntityKind.institution)
        assert len(r.candidates) == 1
        c = r.candidates[0]
        assert c.canonical == "上海银行股份有限公司"
        assert c.matched_via == "L1_exact"
        assert c.score == 1.0

    def test_short_alias(self) -> None:
        r = resolve("上海银行", EntityKind.institution)
        assert len(r.candidates) == 1
        assert r.candidates[0].matched_via == "L1_exact"

    def test_alias_pinyin_abbrev(self) -> None:
        r = resolve("SHB", EntityKind.institution)
        assert len(r.candidates) == 1
        assert r.candidates[0].canonical == "上海银行股份有限公司"

    def test_case_insensitive(self) -> None:
        r = resolve("shb", EntityKind.institution)
        assert len(r.candidates) == 1
        assert r.candidates[0].matched_via == "L1_exact"

    def test_whitespace_tolerant(self) -> None:
        r = resolve("  上海银行  ", EntityKind.institution)
        assert len(r.candidates) == 1
        assert r.candidates[0].matched_via == "L1_exact"

    def test_product_kind(self) -> None:
        r = resolve("百云", EntityKind.product)
        assert len(r.candidates) == 1
        assert r.candidates[0].canonical == "百云系列"
        assert r.candidates[0].db_key == {"pcat_l1": "百云"}


class TestL2Fuzzy:
    def test_typo_close_to_alias(self) -> None:
        # Common Chinese typo
        r = resolve("上海银 行", EntityKind.institution)  # extra space
        assert r.candidates  # should fuzzy-match
        assert r.candidates[0].matched_via in ("L1_exact", "L2_fuzzy")

    def test_partial_match_returns_top_n(self) -> None:
        r = resolve(
            "京东", EntityKind.institution, top_n=3, fuzzy_threshold=70
        )
        # 京东 should fuzzy-match to multiple Chongqing JD-named entities
        assert r.candidates
        assert all(c.score >= 0.70 for c in r.candidates)

    def test_below_threshold_no_candidates(self) -> None:
        r = resolve("完全不相关的名字xyz", EntityKind.institution)
        assert r.candidates == []
        assert any("no L1 or L2 hit" in n for n in r.notes)

    def test_threshold_param_lowers_bar(self) -> None:
        # With permissive threshold even loose matches surface
        r = resolve(
            "银行", EntityKind.institution, fuzzy_threshold=50, top_n=5
        )
        # Multiple banks share "银行" tail
        assert len(r.candidates) >= 1


class TestNotesAndMetadata:
    def test_l1_exact_note(self) -> None:
        r = resolve("上海银行", EntityKind.institution)
        assert any("L1 exact" in n for n in r.notes)

    def test_metadata_industry_for_institution(self) -> None:
        r = resolve("上海银行", EntityKind.institution)
        assert r.candidates[0].metadata["industry"] == "商业银行"

    def test_metadata_codename_attached(self) -> None:
        r = resolve("上海银行", EntityKind.institution)
        # codebook fixture has CUST_a1b2 for 上海银行股份有限公司
        assert r.candidates[0].metadata["codename"] == "CUST_a1b2"

    def test_default_threshold_constant(self) -> None:
        assert DEFAULT_FUZZY_THRESHOLD == 85


class TestEntityLookupTool:
    def test_envelope_shape(self) -> None:
        out = entity_lookup("上海银行")
        assert out["query"] == "上海银行"
        assert out["kind"] == "institution"
        assert isinstance(out["candidates"], list)
        assert len(out["candidates"]) == 1
        c = out["candidates"][0]
        assert set(c) == {
            "canonical",
            "aliases",
            "matched_via",
            "score",
            "db_key",
            "metadata",
        }

    def test_kind_string_accepted(self) -> None:
        out = entity_lookup("百云", kind="product")
        assert out["kind"] == "product"
        assert out["candidates"][0]["db_key"] == {"pcat_l1": "百云"}

    def test_invalid_kind_raises(self) -> None:
        with pytest.raises(ValueError):
            entity_lookup("foo", kind="invalid")  # type: ignore[arg-type]

    def test_no_match_returns_empty_with_note(self) -> None:
        out = entity_lookup("xyzzy_no_match", fuzzy_threshold=99)
        assert out["candidates"] == []
        assert any("no L1 or L2 hit" in n for n in out["notes"])


class TestRegistration:
    def test_entity_lookup_in_all_tools(self) -> None:
        from mj_agent.tools import ALL_TOOLS

        names = [t.__name__ for t in ALL_TOOLS]
        assert "entity_lookup" in names
        # Per system prompt v1.5 default ordering: catalog + entity recall
        # comes before SQL execute
        assert names.index("entity_lookup") < names.index("execute_sql")
