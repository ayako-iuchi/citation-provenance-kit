"""Tests for tools/citelint.py. Run: python3 -m pytest tests -q"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from citelint import lint  # noqa: E402


def checks(text, fmt="markdown", lang="en"):
    return [f.check for f in lint(text, fmt, lang)]


LOG = "## A-2 The log\n\n| # | Error | Rule |\n| --- | --- | --- |\n| 1 | a | b |\n| 2 | c | d |\n\n"


def test_undefined_log_token():
    assert checks(LOG + "Log references: unverified matter → X-01.\n") == ["C1"]


def test_defined_log_token_in_prose_is_accepted():
    assert checks(LOG + "X-01 is an abstention.\n\nLog references: → X-01.\n") == []


def test_reference_to_missing_entry():
    assert checks(LOG + "Log references: → #2, → #7.\n") == ["C1"]


def test_quoted_defect_is_not_a_defect():
    assert checks(LOG + "| 3 | Appendix B cited “X-01”, defined nowhere | — |\n") == []


def test_count_above():
    doc = "## 9. Limits\n\n### 9-1 a\n\n### 9-2 b\n\n### 9-3 note\n\nOne of the three above is new.\n"
    assert checks(doc) == ["C2"]
    assert checks(doc.replace("three above", "two above")) == []


def test_count_above_japanese():
    doc = "## 9. 限界\n\n### 9-1 a\n\n### 9-2 b\n\n### 9-3 注記\n\n上記3つのうち1つは新しい。\n"
    assert checks(doc, "rendered", "ja") == ["C2"]


def test_drafting_note():
    assert checks("The range stands. §7 should be amended accordingly.\n") == ["C3"]
    assert checks("See [v1.2 LINK].\n") == ["C3"]


def test_contents_without_heading():
    doc = "### Contents\n\n- The problem\n\n- Appendix A — The log\n\n## 1. The problem\n\ntext\n"
    assert checks(doc) == ["C4"]


def test_notation_vocabulary_and_grade():
    assert checks("x [wording: A | commencement: —]\n") == []
    assert checks("x [phrasing: A | commencement: —]\n") == ["C5"]
    assert checks("x [wording: E]\n") == ["C5"]
    assert checks("x ［語: A｜施行: —］\n", "rendered", "ja") == []


def test_markup_leaks_in_rendered_text_only():
    rendered = "&nbsp;&nbsp;Appendix A\n\nGrade `A` applies.\n\n| a | b |\n| :-: | --- |\n|  |  |\n"
    assert sorted(checks(rendered, "rendered")) == ["C6", "C6", "C6", "C6"]
    assert checks("| a | b |\n| :-: | --- |\n| 1 | 2 |\n", "markdown") == []
