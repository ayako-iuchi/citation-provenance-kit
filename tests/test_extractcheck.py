"""Tests for tools/extractcheck.py (kit v1.9)."""
import glob
import json
import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import extractcheck  # noqa: E402

EXAMPLES = sorted(glob.glob(os.path.join(ROOT, "examples", "extraction_2026-07-24", "*.json")))
SCHEMA = os.path.join(ROOT, "schema", "extraction.schema.json")


def report(**kw):
    r = {"id": "t", "source": {"title": "a test source"}, "items": []}
    r.update(kw)
    return r


def flagged(result, check="X2"):
    return {(f["kind"], f["identifier"]) for f in result["flags"] if f["check"] == check}


def test_dates_in_different_forms_are_one_date():
    forms = ["the 24th March, 2021", "24.03.2021", "2021年3月24日", "2021-03-24", "March 24, 2021", "2021.03.24"]
    for form in forms:
        assert ("date", "2021-03-24") in extractcheck.identifiers(form), form


def test_gazette_numbers_are_normalised():
    assert ("gazette", "G.S.R. 803(E)") in extractcheck.identifiers("G.S.R. 803 (E), dated")
    assert ("gazette", "S.O. 5458(E)") in extractcheck.identifiers("S.O. 5458 (E)")


def test_memorandum_numbers_keep_their_form():
    ids = extractcheck.identifiers("F./1/9/2021-PPD and F.1/1/2021-PPD")
    assert ("file number", "F./1/9/2021-PPD") in ids and ("file number", "F.1/1/2021-PPD") in ids


@pytest.mark.parametrize("text", ["F.1/1/2021–PPD", "F.No.1/1/2021-PPD", "F No. 1/1/2021-PPD", "F. 1/1/2021-PPD"])
def test_memorandum_number_variants(text):
    assert ("file number", "F.1/1/2021-PPD") in extractcheck.identifiers(text)


def test_titles_drop_leading_words_and_keep_the_year():
    ids = extractcheck.identifiers("In the Companies (Accounts) Rules, 2014,- and Companies (Accounts) Amendment Rules, 2021")
    assert ("title", "companies (accounts) rules, 2014") in ids
    assert ("title", "companies (accounts) amendment rules, 2021") in ids


def test_japanese_article_numbers():
    assert ("条", "52(1)(q)") in extractcheck.identifiers("インド著作権法52条(1)(q)により")
    assert ("条", "52(1)(q)") in extractcheck.identifiers("52条（1）（q）")
    assert ("条", "52(1)") in extractcheck.identifiers("第52条第1項")
    assert ("条", "3-2") in extractcheck.identifiers("3条の2")
    assert not extractcheck.identifiers("4条件を満たす")


def test_a_japanese_jo_is_shown_by_a_section_of_the_same_number():
    r = report(items=[{"n": 1, "target": "x", "status": "found", "page_pdf": "1",
                       "quotes": [{"text": "persons mentioned in section 195 of the Income Tax Act"}],
                       "remarks": ["195条の源泉徴収義務"]}])
    assert not extractcheck.check(r)["flags"]


def test_law_report_citations_ignore_the_court_tag():
    assert ("report", "(2011) 245 CTR 481") in extractcheck.identifiers("[(2011) 245 CTR (Kar) 481]")


def test_a_paragraph_is_shown_by_a_quotation_that_begins_it():
    r = report(items=[{"n": 1, "target": "conclusion", "status": "found", "page_pdf": "115",
                       "quotes": [{"text": "168. Given the definition. 169. Our answer. 170. The appeals"}],
                       "remarks": ["para 168–170"]}])
    assert not extractcheck.check(r)["flags"]
    r["items"][0]["quotes"][0]["text"] = "168. Given the definition"
    assert flagged(extractcheck.check(r)) == {("paragraph", "para 169"), ("paragraph", "para 170")}


def test_identifier_shown_by_a_footnote_is_not_flagged():
    r = report(items=[{"n": 1, "target": "Rule 3(1)", "status": "not_in_source", "search_record": ["searched"],
                       "footnotes": [{"text": "amended vide G.S.R. 205(E), dated the 24th March, 2021"}],
                       "remarks": ["G.S.R. 205(E) dated 24.03.2021 is mentioned"]}])
    assert not extractcheck.check(r)["flags"]


def test_identifier_from_memory_is_flagged():
    r = report(items=[{"n": 1, "target": "Rule 11(g)", "status": "not_in_source", "search_record": ["0 hits"],
                       "remarks": ["Rule 11(g) was inserted by G.S.R. 206(E)"]}])
    assert flagged(extractcheck.check(r)) == {("gazette", "G.S.R. 206(E)")}


def test_identifier_given_by_the_request_is_not_flagged():
    r = report(items=[{"n": 1, "target": "OM F.1/1/2021-PPD", "status": "not_in_source",
                       "search_record": ["F.1/1/2021: 0 hits"], "remarks": ["F.1/1/2021-PPD is not in this PDF"]}])
    result = extractcheck.check(r)
    assert not result["flags"] and result["identifiers"]["given"] == 1


def test_declared_outside_is_counted_not_flagged():
    r = report(outside=[{"text": "G.S.R. 206(E) inserted Rule 11(g)", "origin": "memory"}],
               remarks=["see G.S.R. 206(E)"],
               items=[{"n": 1, "target": "x", "status": "not_in_source", "search_record": ["0 hits"]}])
    result = extractcheck.check(r)
    assert not result["flags"] and result["identifiers"]["declared"] == 1


def test_outside_text_itself_is_not_checked():
    r = report(outside=[{"text": "Companies (Accounts) Amendment Rules, 2021", "origin": "memory"}], items=[])
    assert not extractcheck.check(r)["flags"]


def test_departures_and_source_fields_are_checked():
    r = report(source={"edition": "in force from 1 April 2014"}, departures=["exempt under 52条(1)(q)"], items=[])
    assert flagged(extractcheck.check(r)) == {("date", "2014-04-01"), ("条", "52(1)(q)")}


def test_not_in_source_needs_a_search_record():
    r = report(items=[{"n": 1, "target": "x", "status": "not_in_source"}])
    assert [f["check"] for f in extractcheck.check(r)["flags"]] == ["X3"]


def test_found_needs_a_page():
    r = report(items=[{"n": 1, "target": "x", "status": "found", "quotes": [{"text": "a"}]}])
    assert [f["check"] for f in extractcheck.check(r)["flags"]] == ["X4"]


def test_quote_on_its_page(tmp_path):
    src = tmp_path / "s.txt"
    src.write_text("first page\fThe Rule  says\nthis.\fthird", encoding="utf-8")
    pages = extractcheck.read_source(str(src))
    ok = report(items=[{"n": 1, "target": "x", "status": "found", "page_pdf": "2", "quotes": [{"text": "The Rule says this."}]}])
    assert not extractcheck.check(ok, pages)["flags"]
    wrong = report(items=[{"n": 1, "target": "x", "status": "found", "page_pdf": "3", "quotes": [{"text": "The Rule says this."}]}])
    msg = [f["message"] for f in extractcheck.check(wrong, pages)["flags"] if f["check"] == "X1"]
    assert msg == ["not on page pdf 3; found on PDF page 2"]
    absent = report(items=[{"n": 1, "target": "x", "status": "found", "page_pdf": "2", "quotes": [{"text": "The Rule says that."}]}])
    assert "not found in the source" in extractcheck.check(absent, pages)["flags"][0]["message"]


def test_quote_on_a_page_range_and_printed_page(tmp_path):
    src = tmp_path / "p.json"
    src.write_text(json.dumps({"pages": [{"pdf_page": 1, "printed_page": "24", "text": "alpha"},
                                         {"pdf_page": 2, "printed_page": "25", "text": "beta gamma"}]}), encoding="utf-8")
    pages = extractcheck.read_source(str(src))
    r = report(items=[{"n": 1, "target": "x", "status": "found", "page_printed": "24〜25",
                       "quotes": [{"text": "beta gamma"}]}])
    assert not extractcheck.check(r, pages)["flags"]


def test_excerpt_is_checked_in_parts(tmp_path):
    src = tmp_path / "s.txt"
    src.write_text("one two three four five", encoding="utf-8")
    pages = extractcheck.read_source(str(src))
    r = report(items=[{"n": 1, "target": "x", "status": "found", "page_pdf": "1",
                       "quotes": [{"text": "one two [...] five", "excerpt": True}]}])
    assert not extractcheck.check(r, pages)["flags"]
    r["items"][0]["quotes"][0]["excerpt"] = False
    assert extractcheck.check(r, pages)["flags"][0]["check"] == "X1"


def test_pdflines_source_is_read(tmp_path):
    src = tmp_path / "lines.json"
    src.write_text(json.dumps({"pages": [{"printed_page": 188, "lines": [{"y": 1, "h": 15, "text": "6.18 Since"}]}]}), encoding="utf-8")
    assert extractcheck.read_source(str(src)) == [{"pdf_page": None, "printed_page": "188", "text": "6.18 Since"}]
    assert extractcheck.read_source(str(src), 10)[0]["pdf_page"] == 10


def test_identifier_in_source_text_is_not_flagged(tmp_path):
    src = tmp_path / "s.txt"
    src.write_text("Notification G.S.R. 846(E)", encoding="utf-8")
    r = report(remarks=["this is G.S.R. 846(E)"], items=[])
    assert flagged(extractcheck.check(r)) == {("gazette", "G.S.R. 846(E)")}
    result = extractcheck.check(r, extractcheck.read_source(str(src)))
    assert not result["flags"] and result["identifiers"]["in source"] == 1


def test_exit_codes(tmp_path, capsys):
    clean = tmp_path / "clean.json"
    clean.write_text(json.dumps(report(items=[])), encoding="utf-8")
    assert extractcheck.main([str(clean)]) == 0
    dirty = tmp_path / "dirty.json"
    dirty.write_text(json.dumps(report(remarks=["G.S.R. 1(E)"], items=[])), encoding="utf-8")
    assert extractcheck.main([str(dirty)]) == 1
    for bad_report in ({"items": [{"n": 1, "target": "x", "status": "maybe"}], "id": "b", "source": {}},
                       {"id": "x", "items": [1], "source": {}},
                       {"id": "x", "source": "s", "items": []},
                       {"id": "x", "source": {}, "items": [], "remarks": "G.S.R. 1(E)"},
                       {"id": "x", "source": {}, "items": [], "remark": ["G.S.R. 1(E)"]},
                       {"id": "x", "items": []}):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps(bad_report), encoding="utf-8")
        assert extractcheck.main([str(bad)]) == 2, bad_report
    src = tmp_path / "src.json"
    src.write_text(json.dumps({"pages": [1]}), encoding="utf-8")
    assert extractcheck.main([str(clean), "--source", str(src)]) == 2
    src.write_text(json.dumps([{"text": "x"}]), encoding="utf-8")
    assert extractcheck.main([str(clean), "--source", str(src)]) == 2
    assert extractcheck.main([str(clean), str(dirty), "--source", str(clean)]) == 2
    capsys.readouterr()


def test_json_output(tmp_path, capsys):
    p = tmp_path / "r.json"
    p.write_text(json.dumps(report(remarks=["G.S.R. 1(E)"], items=[])), encoding="utf-8")
    extractcheck.main([str(p), "--json"])
    out = json.loads(capsys.readouterr().out)
    assert out[0]["identifiers"]["not shown"] == 1


def _allowed(schema_obj, data, path="$"):
    """Check that data uses only the properties the schema allows (the schema's additionalProperties: false)."""
    errors = []
    if isinstance(data, dict) and "properties" in schema_obj:
        for key in data:
            if key not in schema_obj["properties"]:
                errors.append("{}.{}".format(path, key))
            else:
                errors += _allowed(schema_obj["properties"][key], data[key], path + "." + key)
        for key in schema_obj.get("required", []):
            if key not in data:
                errors.append("{} missing {}".format(path, key))
    elif isinstance(data, list) and "items" in schema_obj:
        sub = schema_obj["items"]
        for i, x in enumerate(data):
            errors += _allowed(sub, x, "{}[{}]".format(path, i))
    return errors


def _resolve(schema):
    defs = schema.get("$defs", {})

    def walk(node):
        if isinstance(node, dict):
            if "$ref" in node:
                return walk(defs[node["$ref"].split("/")[-1]])
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node
    return walk(schema)


def test_examples_fit_the_schema():
    with open(SCHEMA, encoding="utf-8") as f:
        schema = _resolve(json.load(f))
    assert EXAMPLES
    for path in EXAMPLES:
        for r in extractcheck.load(path):
            assert _allowed(schema, r) == [], path


def test_the_four_threads_as_published():
    """The flags and counts Hypothetical Technical Blog #27 reports. If a transcription changes, this changes."""
    results = {r["id"].split(" ")[0] + (" ERGO" if "ERGO" in r["id"] else ""): extractcheck.check(r)
               for path in EXAMPLES for r in extractcheck.load(path)}
    acc = results["companies-accounts-rules"]
    assert ("gazette", "G.S.R. 206(E)") in flagged(acc)
    assert ("title", "companies (accounts) amendment rules, 2021") in flagged(acc)
    assert ("gazette", "G.S.R. 205(E)") not in flagged(acc)
    ergo = results["engineering-analysis ERGO"]
    assert ("report", "(2011) 245 CTR 481") in flagged(ergo)  # in code marks, which do not count
    assert ("case number", "C.A. 8733-8734/2018") in flagged(ergo)
    assert ("section", "section 14(b)(ii)") in flagged(ergo)
    assert ("rule", "rule 192") in flagged(results["gfr-2017"])
    assert ("file number", "F.7/10/2021-PPD") in flagged(results["gfr-2017"])
    assert ("file number", "F./1/9/2021-PPD") not in flagged(results["gfr-2017"])
    assert ("gazette", "G.S.R. 846(E)") in flagged(results["dpdp-rules"])
    assert flagged(results["engineering-analysis"]) == {("report", "AIRONLINE 2021 SC 102")}
    assert ("条", "52(1)(q)") in flagged(ergo)
    assert {k: v["identifiers"]["not shown"] for k, v in results.items()} == {
        "companies-accounts-rules": 7, "dpdp-rules": 4, "engineering-analysis": 1,
        "engineering-analysis ERGO": 15, "gfr-2017": 11}


@pytest.mark.parametrize("text", ["本PDFはRule 3(1)を含む", "但書はG.S.R. 205(E)が挿入", "改正はF.1/1/2021-PPDによる",
                                  "施行は1st April 2014に", "本PDFはCompanies (Accounts) Rules, 2014のみ"])
def test_identifiers_next_to_japanese_text(text):
    assert extractcheck.identifiers(text)


@pytest.mark.parametrize("text,iso", [("1st day of April, 2022", "2022-04-01"), ("29-10-2021", "2021-10-29"),
                                      ("29/10/2021", "2021-10-29"), ("2nd March,2021", "2021-03-02"),
                                      ("MARCH 2, 2021", "2021-03-02"), ("2 Sept. 2021", "2021-09-02")])
def test_more_date_forms(text, iso):
    assert ("date", iso) in extractcheck.identifiers(text)


def test_a_month_and_year_is_not_a_date():
    assert not extractcheck.identifiers("Sept 2021")


def test_titles_do_not_swallow_what_comes_before():
    assert extractcheck.identifiers("Schedule III of the Companies Act, 2013") == {("title", "companies act, 2013")}
    assert extractcheck.identifiers("The Gazette of India and the Companies Act, 2013") == {("title", "companies act, 2013")}
    assert extractcheck.identifiers("GENERAL FINANCIAL RULES 2017") == {("title", "general financial rules, 2017")}
    assert ("rule", "rule 2017") not in extractcheck.identifiers("General Financial Rules 2017")


def test_a_title_is_shown_by_a_longer_title_that_ends_with_it():
    r = report(items=[{"n": 1, "target": "x", "status": "found", "page_pdf": "1",
                       "quotes": [{"text": "under the Companies Act, 2013"}],
                       "remarks": ["see Schedule III of the Companies Act, 2013"]}])
    assert not extractcheck.check(r)["flags"]


def test_lists_and_ranges_are_expanded():
    ids = extractcheck.identifiers("Rules 1, 2 and 17 to 21")
    assert {("rule", "rule " + n) for n in ("1", "2", "17", "18", "19", "20", "21")} == ids
    assert {("section", "section 9"), ("section", "section 195")} == extractcheck.identifiers("sections 9 and 195")


def test_a_more_specific_provision_shows_a_general_one():
    r = report(items=[{"n": 1, "target": "x", "status": "found", "page_pdf": "1",
                       "quotes": [{"text": "in the proviso to sub-rule (1) of rule 3"}],
                       "remarks": ["Rule 3(1) has a proviso", "Rule 3 is about books of account"]}])
    assert not extractcheck.check(r)["flags"]
    r["items"][0]["remarks"] = ["Rule 3(2) says"]
    assert flagged(extractcheck.check(r)) == {("rule", "rule 3(2)")}


def test_section_headings_of_the_gazette_are_not_sections():
    assert not extractcheck.identifiers("PART II—Section 3—Sub-section (i)")


def test_a_rule_number_before_a_heading_is_not_a_paragraph():
    assert ("paragraph", "para 149") not in extractcheck.identifiers("Rule 149. Government e-Market", verbatim=True)


@pytest.mark.parametrize("text,ident", [("GSR 205(E)", ("gazette", "G.S.R. 205(E)")),
                                        ("SO 5458(E)", ("gazette", "S.O. 5458(E)")),
                                        ("¶ 6.21", ("paragraph", "para 6.21")),
                                        ("Para 4", ("paragraph", "para 4")),
                                        ("u/s 195", ("section", "section 195")),
                                        ("(2012) 345 I.T.R. 494", ("report", "(2012) 345 ITR 494")),
                                        ("AIR 2021 SC 102", ("report", "AIR 2021 SC 102")),
                                        ("[2021] 125 taxmann.com 42", ("report", "[2021] 125 taxmann.com 42"))])
def test_more_identifier_forms(text, ident):
    assert ident in extractcheck.identifiers(text)


def test_the_search_record_is_the_extractors_own_account():
    r = report(items=[{"n": 1, "target": "Rule 11(g)", "status": "not_in_source",
                       "search_record": ["searched for G.S.R. 206(E): 0 hits"],
                       "remarks": ["Rule 11(g) was inserted by G.S.R. 206(E)"]}])
    result = extractcheck.check(r)
    assert {f["where"] for f in result["flags"]} == {"item 1 remark 1", "item 1 search 1"}
    r["items"][0]["search_record"] = ["one hit: 「Inserted vide G.S.R. 206(E)」"]
    result = extractcheck.check(r)
    assert not result["flags"] and result["identifiers"]["shown"] == 1


def test_a_passage_in_quotation_marks_counts_as_shown():
    for marks in ("「{}」", "“{}”", '"{}"'):
        r = report(remarks=["the note reads " + marks.format("Deleted vide OM No. F.1/26/2018-PPD"),
                            "so F.1/26/2018-PPD deleted it"], items=[])
        assert not extractcheck.check(r)["flags"], marks


def test_code_marks_do_not_count_as_shown():
    r = report(remarks=["the citation is `(2012) 345 ITR 494`"], items=[])
    assert flagged(extractcheck.check(r)) == {("report", "(2012) 345 ITR 494")}


def test_a_search_term_in_quotation_or_code_marks_is_not_shown():
    for term in ('"G.S.R. 205(E)"', "`G.S.R. 205(E)`"):
        r = report(items=[{"n": 1, "target": "x", "status": "not_in_source",
                           "search_record": ["string search for {} → 0 hits".format(term)],
                           "remarks": ["it was inserted by G.S.R. 205(E)"]}])
        assert ("gazette", "G.S.R. 205(E)") in flagged(extractcheck.check(r)), term
    r = report(items=[{"n": 1, "target": "x", "status": "not_in_source",
                       "search_record": ["one hit: 「Inserted vide G.S.R. 205(E)」"],
                       "remarks": ["it was inserted by G.S.R. 205(E)"]}])
    assert not extractcheck.check(r)["flags"]


def test_case_numbers():
    assert extractcheck.identifiers("CIVIL APPEAL NOS. 8733-8734 OF 2018") == {("case number", "C.A. 8733-8734/2018")}
    assert extractcheck.identifiers("C.A. No. 8990/2018") == {("case number", "C.A. 8990/2018")}
    assert extractcheck.identifiers("SLP(C) No. 450/2019") == {("case number", "SLP(C) 450/2019")}


def test_lists_with_japanese_separators_and_capital_sec():
    assert ("section", "section 52(1)(aa)") in extractcheck.identifiers("改正Sec.14(b)(ii)・52(1)(aa)")
    assert ("section", "section 3(i)") in extractcheck.identifiers("SEC. 3(i)")
    assert not extractcheck.identifiers("PART II—SEC. 3(i)")


def test_partial_needs_a_page():
    r = report(items=[{"n": 1, "target": "x", "status": "partial"}])
    assert extractcheck.check(r)["flags"][0]["message"] == "reported partial with no page"
    r["items"][0]["page_pdf"] = "1"
    assert not extractcheck.check(r)["flags"]


def test_reports_are_checked_one_at_a_time(tmp_path):
    a = report(id="a", items=[{"n": 1, "target": "x", "status": "found", "page_pdf": "1",
                                "quotes": [{"text": "168. Given that"}]}])
    b = report(id="b", remarks=["para 168"], items=[])
    p = tmp_path / "ab.json"
    p.write_text(json.dumps([a, b]), encoding="utf-8")
    results = [extractcheck.check(r) for r in extractcheck.load(str(p))]
    assert not results[0]["flags"] and flagged(results[1]) == {("paragraph", "para 168")}


def test_circled_numbers_are_labels():
    assert extractcheck.identifiers("②195条の結論") == {("条", "195")}


def test_expected_is_not_given():
    r = report(items=[{"n": 1, "target": "Rule 11(g)", "expected": "inserted by G.S.R. 206(E)",
                       "status": "not_in_source", "search_record": ["0 hits"],
                       "remarks": ["G.S.R. 206(E)"]}])
    assert flagged(extractcheck.check(r)) == {("gazette", "G.S.R. 206(E)")}


def test_the_cover_as_quoted_shows_what_it_says():
    r = report(source={"title": "GENERAL FINANCIAL RULES 2017 Updated up to 31.07.2024",
                       "cover": [{"text": "GENERAL FINANCIAL RULES 2017 / Updated up to 31.07.2024", "page_pdf": "1"}]},
               items=[])
    assert not extractcheck.check(r)["flags"]


def test_counts_are_of_distinct_identifiers():
    r = report(source={"title": "G.S.R. 9(E)", "edition": "G.S.R. 9(E)"}, remarks=["G.S.R. 9(E)"], items=[])
    result = extractcheck.check(r)
    assert result["identifiers"]["not shown"] == 1 and len(result["flags"]) == 3


def test_pdf_and_printed_pages_are_not_confused(tmp_path):
    src = tmp_path / "p.json"
    src.write_text(json.dumps({"pages": [{"pdf_page": 1, "printed_page": "2", "text": "alpha text"},
                                         {"pdf_page": 2, "printed_page": "3", "text": "beta text"}]}), encoding="utf-8")
    pages = extractcheck.read_source(str(src))
    r = report(items=[{"n": 1, "target": "x", "status": "found", "page_pdf": "2", "quotes": [{"text": "alpha text"}]}])
    assert [f["check"] for f in extractcheck.check(r, pages)["flags"]] == ["X1"]
    r["items"][0] = {"n": 1, "target": "x", "status": "found", "page_printed": "2", "quotes": [{"text": "alpha text"}]}
    assert not extractcheck.check(r, pages)["flags"]


def test_page_lists_with_commas_and_quotes_across_pages(tmp_path):
    src = tmp_path / "s.txt"
    src.write_text("a\fb\fc and the quote begins\fand ends here\fe\f" + "\f".join("x" * 110), encoding="utf-8")
    pages = extractcheck.read_source(str(src))
    r = report(items=[{"n": 1, "target": "x", "status": "found", "page_pdf": "1–5, 115",
                       "quotes": [{"text": "the quote begins and ends here"}, {"text": "c and the"}]}])
    assert not extractcheck.check(r, pages)["flags"]


def test_line_end_hyphens_in_the_source(tmp_path):
    src = tmp_path / "s.txt"
    src.write_text("shall remain accessi-\nble in India", encoding="utf-8")
    r = report(items=[{"n": 1, "target": "x", "status": "found", "page_pdf": "1",
                       "quotes": [{"text": "shall remain accessible in India"}]}])
    assert not extractcheck.check(r, extractcheck.read_source(str(src)))["flags"]


def test_found_with_pages_on_every_quote_needs_no_item_page():
    r = report(items=[{"n": 1, "target": "x", "status": "found", "quotes": [{"text": "a", "page_pdf": "3"}]}])
    assert not extractcheck.check(r)["flags"]
    r["items"][0]["status"] = "undeterminable"
    r["items"][0]["quotes"] = []
    assert extractcheck.check(r)["flags"][0]["message"] == "reported undeterminable with no page"


def test_report_option_picks_one_report_for_source(tmp_path, capsys):
    two = tmp_path / "two.json"
    two.write_text(json.dumps([report(id="a", items=[]), report(id="b", items=[])]), encoding="utf-8")
    src = tmp_path / "s.txt"
    src.write_text("text", encoding="utf-8")
    assert extractcheck.main([str(two), "--source", str(src)]) == 2
    assert extractcheck.main([str(two), "--source", str(src), "--report", "b"]) == 0
    assert extractcheck.main([str(two), "--report", "c"]) == 2
    capsys.readouterr()


def test_examples_validate_against_the_schema():
    jsonschema = pytest.importorskip("jsonschema")
    with open(SCHEMA, encoding="utf-8") as f:
        schema = json.load(f)
    for path in EXAMPLES:
        for r in extractcheck.load(path):
            jsonschema.validate(r, schema)
