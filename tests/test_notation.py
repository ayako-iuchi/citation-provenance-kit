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


@pytest.mark.parametrize("dash", ["-", "–", "‒", "―", "−", "ー", "－"])
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


def test_example_records_are_what_the_parser_reads():
    for rec in load_example():
        again = one(rec["text"])
        assert (again["form"], again["slots"]) == (rec["form"], rec["slots"]), rec["id"]


def test_example_passes_every_mechanical_check():
    for rec in load_example():
        errors = [c for c, sev, _ in notation.check(rec) if sev == "error"]
        assert errors == [], (rec["id"], errors)


# --- review of c5d12de (2026-10-20) ------------------------------------------

def test_markdown_links_are_not_annotations():
    text = "see [A](http://x) and ![B](img.png) and [C][ref]\n[A]: http://y\n"
    assert list(notation.parse(text)) == []
    assert notation.rewrite(text, "ja") == text


def test_prose_brackets_with_colons_are_left_alone():
    assert list(notation.parse("[Edit: typo] [Updated: 2024] [TODO: fix] [Note: B]")) == []


def test_lone_wrong_dash_is_not_an_annotation():
    assert list(notation.parse("[-] [ー]")) == []


def test_plain_dash_gets_n7():
    assert [c for c, _, _ in notation.check(one("[—]"))] == ["N7"]


@pytest.mark.parametrize("text", ["[wording: A, page: B]", "[wording: A |]",
                                  "[wording: A || page: B]", "[wording: A B]"])
def test_n0_malformed(text):
    assert codes(text) == ["N0"]


def test_n0_is_not_rewritten():
    assert notation.rewrite("x [wording: A, page: B] y", "ja") == "x [wording: A, page: B] y"


def test_extension_component(tmp_path):
    comps = notation.load_components(extend=["restatement-status=修正再表示"])
    r = next(notation.parse("[restatement-status: A | figure: B]", comps))
    assert r["slots"][0]["component"] == "restatement-status" and r["slots"][0]["volatile"] is None
    assert notation.check(r) == []
    p = tmp_path / "d.md"
    p.write_text("[restatement-status: A | figure: B]", encoding="utf-8")
    assert notation.main([str(p)]) == 1
    assert notation.main([str(p), "--extend", "restatement-status"]) == 0


def test_blank_line_stops_an_annotation():
    assert list(notation.parse("[wording: A |\n\n page: B]")) == []


def test_markdown_option_skips_code():
    text = "real [wording: A | page: —]\n```\n[wording: A | page: A]\n```\nand `[wording: A | page: A]`\n"
    assert len(list(notation.parse(text))) == 3
    recs = list(notation.parse(text, markdown=True))
    assert [r["text"] for r in recs] == ["[wording: A | page: —]"]
    assert notation.rewrite(text, "ja", markdown=True).count("［語: A｜頁: —］") == 1


def test_rewrite_keeps_crlf():
    text = "a [wording: A | page: —]\r\nb\r\n"
    assert notation.rewrite(text, "ja") == "a ［語: A｜頁: —］\r\nb\r\n"


def test_cli_modes(tmp_path, capsys):
    p = tmp_path / "d.md"
    p.write_text("[wording: A | page: -]", encoding="utf-8")
    assert notation.main([str(p), "--records"]) == 0
    assert json.loads(capsys.readouterr().out)["slots"][1]["grade"] == "-"
    assert notation.main([str(p), "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["findings"][0]["check"] == "N3"
    assert notation.main([str(p), "--to", "ja"]) == 0
    assert capsys.readouterr().out == "［語: A｜頁: -］"
    assert notation.main([str(tmp_path / "missing.md")]) == 2


def test_vocabulary_is_one_list():
    """The bug of v1.0-v1.4: the Japanese names lived in more than one list."""
    import ast
    import citelint
    src = open(os.path.join(ROOT, "tools", "build_kit.py"), encoding="utf-8").read()
    build = None
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "COMPONENTS" for t in node.targets):
            build = {row[0]: row[1] for row in ast.literal_eval(node.value)}
    csv_names = notation._ja_names()
    assert build == csv_names
    assert set(csv_names) | set(csv_names.values()) == citelint.COMPONENTS["ja"]
    assert set(csv_names) == citelint.COMPONENTS["en"]


# --- second review (15c6fb6, 2026-10-20) -------------------------------------

@pytest.mark.parametrize("text", ["[wording: A | page: —][1]", "[wording: A | page: —][^1]",
                                  "[wording: A | page: —](see note)", "［語: A｜頁: —］(注)",
                                  "[wording: A | page: —]: as printed"])
def test_annotation_followed_by_link_syntax_is_still_read(text):
    assert len(list(notation.parse(text))) == 1


def test_reference_definition_needs_a_url():
    assert list(notation.parse("[A]: https://example.com\n")) == []
    assert len(list(notation.parse("[A]: the grade we gave\n"))) == 1


def test_unmatched_backtick_masks_nothing():
    text = "`stray\n\nreal [wording: A | page: —]\n\nlater `code`\n"
    assert len(list(notation.parse(text, markdown=True))) == 1


def test_fences_follow_commonmark():
    longer = "````\n```\n[wording: A | page: A]\n````\nafter [wording: A | page: —]\n"
    assert [r["text"] for r in notation.parse(longer, markdown=True)] == ["[wording: A | page: —]"]
    unclosed = "before [wording: A | page: —]\n```\n[wording: A | page: A]\n"
    assert [r["text"] for r in notation.parse(unclosed, markdown=True)] == ["[wording: A | page: —]"]


@pytest.mark.parametrize("text", ["[page: 12]", "［日付: 2024年］", "[edition: 3rd ed.]"])
def test_component_named_but_nothing_graded_is_left_alone(text):
    assert list(notation.parse(text)) == []


def test_mixed_bracket_widths_are_malformed():
    assert codes("［wording: A | page: B]") == ["N0"]


# --- third review (d164acf, 2026-10-20) --------------------------------------

@pytest.mark.parametrize("text", ["[wording: E]", "[wording: a]", "[wording: Ａ]", "[wording: A+]"])
def test_single_slot_with_a_wrong_grade_is_reported(text):
    assert codes(text) == ["N2"]


def test_wrong_grades_in_every_slot_are_reported():
    assert codes("[wording: E | page: F]") == ["N2", "N2"]


def test_double_backtick_code_with_a_single_backtick_inside():
    text = "``a`b [wording: A | page: A]`` and [wording: A | page: —]"
    assert [r["text"] for r in notation.parse(text, markdown=True)] == ["[wording: A | page: —]"]
