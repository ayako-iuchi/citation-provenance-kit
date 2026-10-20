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
    assert t["date"]["post"]["status"] == "unexamined" and t["date"]["post"]["other"] == 1
    assert t["date"]["pre"]["status"] == "unexamined" and t["date"]["pre"]["other"] == 1


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
    assert [r["kind"] for r in rows if r["kind"] == "confirmation" and r["phase"] == "post"] == ["confirmation"]


def test_cli_json(capsys):
    assert catchlog.main([EXAMPLE, "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["entries"] == 45 and out["components"]["figure"]["pre"]["status"] == "unexamined"
