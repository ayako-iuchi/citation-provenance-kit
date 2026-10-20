"""Tests for tools/catchlog.py (kit v1.7)."""
import json
import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import catchlog  # noqa: E402

EXAMPLE = os.path.join(ROOT, "examples", "method_paper_v1.2", "catch_log.csv")
COMPS = catchlog.load_components()


def write(tmp_path, text, name="log.csv"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_two_zeros_are_told_apart(tmp_path):
    p = write(tmp_path, "no,component,outcome,phase\n1,wording,corrected,pre\nA,page,confirmed,pre\n")
    t = catchlog.tally(catchlog.read_log(p), COMPS)
    assert t["page"]["pre"]["status"] == "clean"
    assert t["figure"]["pre"]["status"] == "unexamined"
    assert t["page"]["pre"]["corrections"] == t["figure"]["pre"]["corrections"] == 0


def test_corrections_and_confirmations_are_never_added(tmp_path):
    p = write(tmp_path, "no,component,outcome,phase\n1,figure,corrected,post\n2,figure,confirmed,post\n")
    cell = catchlog.tally(catchlog.read_log(p), COMPS)["figure"]["post"]
    assert (cell["corrections"], cell["confirmations"], cell["status"]) == (1, 1, "found")


def test_phases_are_kept_apart(tmp_path):
    p = write(tmp_path, "no,component,outcome,phase\n1,figure,corrected,post\n")
    t = catchlog.tally(catchlog.read_log(p), COMPS)
    assert t["figure"]["pre"]["status"] == "unexamined" and t["figure"]["post"]["status"] == "found"


def test_other_outcomes_are_neither(tmp_path):
    p = write(tmp_path, "no,component,outcome,phase\n1,date,rule sharpened,post\n2,date,abstained,pre\n")
    t = catchlog.tally(catchlog.read_log(p), COMPS)
    assert t["date"]["post"]["status"] == "other-only" and t["date"]["post"]["other"] == 1
    assert t["date"]["pre"]["status"] == "other-only" and t["date"]["pre"]["other"] == 1


def test_workbook_headers_and_values(tmp_path):
    head = "#,Component(s) / 成分,Outcome / 結果,Phase / 公開前／後\n"
    p = write(tmp_path, head + "1,edition → identifier,confirmed (no error found),Pre-release\n")
    t = catchlog.tally(catchlog.read_log(p), COMPS)
    assert t["edition"]["pre"]["status"] == t["identifier"]["pre"]["status"] == "clean"


def test_count_column(tmp_path):
    p = write(tmp_path, "no,component,outcome,phase,count\n1,page,confirmed,pre,12\n")
    assert catchlog.tally(catchlog.read_log(p), COMPS)["page"]["pre"]["confirmations"] == 12


def test_bad_input(tmp_path):
    assert catchlog.main([write(tmp_path, "no,component,outcome\n1,page,corrected\n")]) == 2
    assert catchlog.main([write(tmp_path, "no,component,outcome,phase\n1,page,corrected,later\n")]) == 2
    assert catchlog.main([write(tmp_path, "no,component,outcome,phase\n1,,corrected,pre\n")]) == 2
    assert catchlog.main([str(tmp_path / "missing.csv")]) == 2


# --- the method paper's own log ----------------------------------------------

def example():
    return catchlog.tally(catchlog.read_log(EXAMPLE), COMPS)


def test_example_reproduces_the_papers_tally():
    """§7-2: wording 8, edition 7, identifier/existence/commencement/date/attribution 2,
    dependency 1, page 0, figure 0 (each correction counted under every component it touched)."""
    t = example()
    want = {"wording": 8, "edition": 7, "identifier": 2, "existence": 2, "commencement": 2,
            "date": 2, "attribution": 2, "dependency": 1, "page": 0, "figure": 0, "outside": 3}
    assert {c: t[c]["pre"]["corrections"] for c in want} == want


def test_example_two_zeros_before_release():
    t = example()
    assert t["page"]["pre"]["status"] == "clean" and t["page"]["pre"]["uncounted"]
    assert t["figure"]["pre"]["status"] == "unexamined"


def test_example_figure_after_release():
    """§7-3: since release, two corrections and one confirmation (#26, #27, #34)."""
    cell = example()["figure"]["post"]
    assert (cell["corrections"], cell["confirmations"]) == (2, 1)
    assert cell["entries"]["correction"] == ["26", "27"] and cell["entries"]["confirmation"] == ["34"]


def test_example_post_release_entries_and_editions():
    rows = catchlog.read_log(EXAMPLE)
    post = [r["no"] for r in rows if r["phase"] == "post"]
    assert post == [str(n) for n in range(26, 45)]
    assert [r["no"] for r in rows if r["kind"] == "confirmation" and r["phase"] == "post"] == ["34"]
    import csv as _csv
    with open(EXAMPLE, encoding="utf-8") as f:
        assert [r["no"] for r in _csv.DictReader(f) if r["edition"] == "ja"] == ["43", "44"]


def test_cli_json(capsys):
    assert catchlog.main([EXAMPLE, "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["rows"] == 45 and out["components"]["figure"]["pre"]["status"] == "unexamined"


# --- review of 004638b (2026-10-20) ------------------------------------------

def test_workbook_export_is_read(tmp_path):
    """The Catch log sheet saved as CSV: title rows, two-line headers, the Ex. row, numbered empty rows."""
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.load_workbook(os.path.join(ROOT, "kit", "citation-provenance-kit.xlsx"))
    ws = wb["Catch log"]
    col = {str(c.value).split("\n")[0]: c.column_letter for c in ws[4] if c.value}
    ws[col["Component(s)"] + "6"] = "figure"
    ws[col["Outcome"] + "6"] = "confirmed (no error found)"
    ws[col["Phase"] + "6"] = "Post-release"
    import csv as _csv
    p = tmp_path / "export.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = _csv.writer(f)
        for row in ws.iter_rows(values_only=True):
            w.writerow(["" if v is None else v for v in row])
    rows = catchlog.read_log(str(p))
    assert [(r["no"], r["components"], r["kind"], r["phase"]) for r in rows] == [("1", ["figure"], "confirmation", "post")]


def test_template_example_row_is_skipped():
    p = os.path.join(ROOT, "csv", "catch_log_template.csv")
    assert catchlog.read_log(p) == []


def test_numbered_confirmation_with_empty_count_is_one(tmp_path):
    p = write(tmp_path, "no,component,outcome,phase,count\n7,page,confirmed,pre,\n,page,confirmed,pre,\n")
    cell = catchlog.tally(catchlog.read_log(p))["page"]["pre"]
    assert (cell["confirmations"], cell["uncounted"]) == (2, False)


def test_uncounted_is_explicit(tmp_path):
    p = write(tmp_path, "no,component,outcome,phase,count\nA,page,confirmed,pre,uncounted\n")
    cell = catchlog.tally(catchlog.read_log(p))["page"]["pre"]
    assert (cell["confirmations"], cell["uncounted"], cell["status"]) == (0, True, "clean")
    with pytest.raises(ValueError):
        catchlog.read_log(write(tmp_path, "no,component,outcome,phase,count\n1,page,corrected,pre,uncounted\n"))


@pytest.mark.parametrize("count", ["-3", "0", "2.0", "x"])
def test_bad_counts(tmp_path, count):
    with pytest.raises(ValueError, match="entry '1'"):
        catchlog.read_log(write(tmp_path, f"no,component,outcome,phase,count\n1,page,corrected,pre,{count}\n"))


def test_component_names_are_normalised(tmp_path, capsys):
    p = write(tmp_path, "no,component,outcome,phase\n1,Wording,corrected,pre\n2,語＋帰属,corrected,pre\n3,対象外,deleted,pre\n4,wordng,corrected,pre\n")
    rows = catchlog.read_log(p)
    assert [r["components"] for r in rows] == [["wording"], ["wording", "attribution"], ["outside"], ["wordng"]]
    assert "wordng" in capsys.readouterr().err
    with pytest.raises(ValueError, match="unknown"):
        catchlog.read_log(p, strict=True)


@pytest.mark.parametrize("sep", [" + ", "＋", " → ", ", ", "/", "／"])
def test_separators(tmp_path, sep):
    p = write(tmp_path, f"no,component,outcome,phase\n1,\"edition{sep}date\",corrected,pre\n")
    assert catchlog.read_log(p)[0]["components"] == ["edition", "date"]


@pytest.mark.parametrize("phase,want", [("公開前", "pre"), ("公開後", "post"), ("Pre-release", "pre"), ("post", "post")])
def test_phases(tmp_path, phase, want):
    assert catchlog.read_log(write(tmp_path, f"no,component,outcome,phase\n1,page,corrected,{phase}\n"))[0]["phase"] == want


@pytest.mark.parametrize("phase", ["preliminary", "Postponed", "later", ""])
def test_bad_phases(tmp_path, phase):
    with pytest.raises(ValueError):
        catchlog.read_log(write(tmp_path, f"no,component,outcome,phase\n1,page,corrected,{phase}\n"))


def test_cp932(tmp_path):
    p = tmp_path / "sjis.csv"
    p.write_bytes("no,成分,結果,公開前／後\n1,頁,corrected,公開前\n".encode("cp932"))
    assert catchlog.read_log(str(p))[0]["components"] == ["page"]


def test_empty_file_and_duplicate_columns(tmp_path, capsys):
    assert catchlog.main([write(tmp_path, "")]) == 2
    assert "empty" in capsys.readouterr().err
    assert catchlog.main([write(tmp_path, "no,component,outcome,outcome,phase\n1,page,corrected,corrected,pre\n")]) == 2
    assert catchlog.main([write(tmp_path, "1,page,corrected,pre\n"), "--components", write(tmp_path, "component,ja\n", "c.csv")]) == 2


# --- kit v1.8: --fields ------------------------------------------------------

SERIES = os.path.join(ROOT, "examples", "series_log", "after_v1.2.csv")


def test_fields_counts_the_continuing_log():
    f = catchlog.fields(catchlog.read_log(SERIES, columns_only=True))
    would = f["columns"]["What would have happened had it gone unnoticed"]["post"]
    assert (would["filled"], would["pending"], would["blank"]) == (3, 15, 0)
    assert f["undecided"]["What would have happened had it gone unnoticed"] == [str(n) for n in [45] + list(range(49, 63))]
    assert f["who"] == {"not yet decided": 15, "author chose from assistant's options": 3}
    assert f["columns"]["Duration (minutes)"]["post"]["pending"] == 18


def test_who_column_is_not_the_judgment_column(tmp_path):
    p = write(tmp_path, "no,phase,What would have happened had it gone unnoticed,Who wrote 'what would have happened'?\n1,pre,,author\n")
    f = catchlog.fields(catchlog.read_log(p, columns_only=True))
    assert list(f["undecided"]) == ["What would have happened had it gone unnoticed"]


@pytest.mark.parametrize("value,state", [("", "blank"), ("—", "pending"), ("-", "pending"), ("—（未判断、2026-10-20）", "pending"),
                                          ("（著者が記入）", "pending"), ("TBD", "pending"), ("記録なし", "pending"),
                                          ("A footnote dies", "filled"), ("誤りではなく古い値（著者の判断）", "filled")])
def test_pending_values(tmp_path, value, state):
    p = write(tmp_path, f"no,phase,Stakes\n1,post,{value}\n")
    cell = catchlog.fields(catchlog.read_log(p, columns_only=True))["columns"]["Stakes"]["post"]
    assert cell[state] == 1


def test_fields_cli_and_template(capsys):
    assert catchlog.main([SERIES, "--fields"]) == 0
    out = capsys.readouterr().out
    assert "no decision in 'Stakes': 45, 49" in out
    assert catchlog.main([os.path.join(ROOT, "csv", "catch_log_template.csv"), "--fields", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["rows"] == 0


def test_phase_with_a_note_in_brackets(tmp_path):
    p = write(tmp_path, "no,component,outcome,phase\n1,page,corrected,公開後（キットv1.2は公開済み）\n")
    assert catchlog.read_log(p)[0]["phase"] == "post"


def test_template_has_the_who_column():
    import csv as _csv
    with open(os.path.join(ROOT, "csv", "catch_log_template.csv"), encoding="utf-8-sig") as f:
        head = next(_csv.reader(f))
    assert "Who wrote 'what would have happened'? / 「見逃していたら」を誰が書いたか" in head
    assert head.index("Stakes / 影響の大きさ") + 1 == head.index("Who wrote 'what would have happened'? / 「見逃していたら」を誰が書いたか")
