"""Tests for tools/notation.py (kit v1.5)."""
import json
import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import notation  # noqa: E402

EXAMPLE = os.path.join(ROOT, "examples", "method_paper_v1.2", "annotations.jsonl")


def one(text):
    recs = list(notation.parse(text))
    assert len(recs) == 1, recs
    return recs[0]


def codes(text):
    return [c for c, _, _ in notation.check(one(text))]


# --- reading -----------------------------------------------------------------

def test_english_form_reads_as_typed_slots():
    r = one("as the gazette says [wording: A | commencement: —] and")
    assert r["form"] == "en"
    assert [(s["component"], s["grade"]) for s in r["slots"]] == [("wording", "A"), ("commencement", "—")]


def test_japanese_form_reads_to_the_same_types():
    r = one("官報のとおり［施行: —｜版: B］である")
    assert r["form"] == "ja"
    assert [(s["component"], s["grade"]) for s in r["slots"]] == [("commencement", "—"), ("edition", "B")]


def test_whitespace_is_not_significant():
    a = one("[existence: A | page: B]")
    b = one("［存在: A ｜頁:B］")
    assert [(s["component"], s["grade"]) for s in a["slots"]] == [(s["component"], s["grade"]) for s in b["slots"]]


def test_annotation_broken_across_lines_is_read_with_its_first_line():
    r = one("line one\nsee [figure: A |\n edition: —] here")
    assert r["line"] == 2 and len(r["slots"]) == 2


def test_volatile_follows_components_csv():
    r = one("[wording: A | commencement: —]")
    assert [s["volatile"] for s in r["slots"]] == [False, True]


def test_plain_grade_and_non_annotations():
    assert one("[A]")["form"] == "plain"
    assert list(notation.parse("[sic] [Domain EN LINK] [A — Economic Survey 2020-21, p. 188]")) == []


def test_the_papers_statement_of_the_form_is_not_an_annotation():
    assert list(notation.parse("[component: grade | component: grade] ［成分: 級｜成分: 級］")) == []


# --- the three states --------------------------------------------------------

def test_dash_and_absence_are_different_values():
    with_dash = one("[wording: A | page: —]")
    without = one("[wording: A]")
    assert len(with_dash["slots"]) == 2 and with_dash["slots"][1]["grade"] == "—"
    assert len(without["slots"]) == 1  # page: nothing recorded either way


# --- checks ------------------------------------------------------------------

def test_n1_unknown_component():
    assert "N1" in codes("[wordings: A | page: —]")


def test_n2_grade_outside_scale():
    assert "N2" in codes("[wording: E | page: —]")


@pytest.mark.parametrize("dash", ["-", "–", "―", "−", "ー", "－"])
def test_n3_wrong_dash(dash):
    assert codes(f"[wording: A | page: {dash}]") == ["N3"]


def test_n4_four_slots():
    assert "N4" in codes("[wording: A | page: B | date: C | edition: —]")


def test_n5_duplicate_even_across_languages():
    assert "N5" in codes("[edition: A | edition: —]")
    assert "N5" in codes("［版: A｜edition: —］")


def test_n6_no_divergence():
    assert codes("[wording: A | page: A]") == ["N6"]
    assert codes("[wording: — | page: —]") == ["N6", "N7"]


def test_n7_null_first_is_a_notice():
    r = one("[commencement: — | wording: A]")
    found = notation.check(r)
    assert [(c, sev) for c, sev, _ in found] == [("N7", "notice")]


def test_valid_annotation_has_no_findings():
    assert codes("[wording: A | commencement: B]") == []


def test_exit_status_ignores_notices(tmp_path):
    p = tmp_path / "doc.md"
    p.write_text("[commencement: — | wording: A]", encoding="utf-8")
    assert notation.main([str(p)]) == 0
    p.write_text("[wording: A | page: -]", encoding="utf-8")
    assert notation.main([str(p)]) == 1


# --- rewriting between the two forms -----------------------------------------

def test_round_trip_en_ja_en():
    text = "It is [wording: A | commencement: —] and [existence: A | figure: B]."
    ja = notation.rewrite(text, "ja")
    assert "［語: A｜施行: —］" in ja
    assert notation.rewrite(ja, "en") == text


def test_rewrite_leaves_other_brackets_alone():
    text = "[sic] [A — a source] [Domain EN LINK]"
    assert notation.rewrite(text, "ja") == text


# --- the paper's own annotations ---------------------------------------------

def load_example():
    with open(EXAMPLE, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def test_example_validates_against_schema():
    jsonschema = pytest.importorskip("jsonschema")
    with open(os.path.join(ROOT, "schema", "annotation.schema.json"), encoding="utf-8") as f:
        schema = json.load(f)
    for rec in load_example():
        jsonschema.validate(rec, schema)


def test_example_editions_have_nine_citations_each_in_the_same_order():
    recs = load_example()
    en = [r for r in recs if r["edition"] == "en" and r["use"] == "citation"]
    ja = [r for r in recs if r["edition"] == "ja" and r["use"] == "citation"]
    assert len(en) == len(ja) == 9
    for a, b in zip(en, ja):
        assert [s["grade"] for s in a["slots"]] == [s["grade"] for s in b["slots"]]
        assert [s["component"] for s in a["slots"]] == [s["component"] for s in b["slots"]], (a["id"], b["id"])


def test_wording_is_named_as_in_the_paper():
    # Kit v1.0-v1.4 named it 文言 in components.csv; the paper (§4-2) and citelint say 語.
    assert notation.load_components()["語"] == ("wording", False)
    assert "文言" not in notation.load_components()


def test_example_passes_every_mechanical_check():
    for rec in load_example():
        errors = [c for c, sev, _ in notation.check(rec) if sev == "error"]
        assert errors == [], (rec["id"], errors)
