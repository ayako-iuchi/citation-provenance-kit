"""Tests for tools/pdflines.py and tools/loci.py (kit v1.4).

Each test names a fault a text-only chunker makes on the example chapter
(Economic Survey 2020-21, Vol. 1, ch. 6) and checks that the locus splitter does not.

Run: python3 -m pytest tests
"""
import hashlib
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import loci  # noqa: E402
import pdflines  # noqa: E402

EX = os.path.join(ROOT, "examples", "es2021_ch6")


@pytest.fixture(scope="module")
def doc():
    with open(os.path.join(EX, "lines.json"), encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def split(doc):
    return {l["id"]: l for l in loci.split(doc, read_on="2026-10-20")}


# --- finding 1: a footnote is printed under someone else's sentence ---------------

def test_footnote_6_is_its_own_locus_anchored_in_6_20(split):
    fn6 = split["es2021-ch6-fn6"]
    assert fn6["kind"] == "footnote"
    assert fn6["anchored_in"] == "es2021-ch6-p6.20"
    assert fn6["snapshot"]["wording"].startswith("QCI conducted a pilot study as a part of World Bank Technical Assessment")
    assert "es2021-ch6-fn6" in split["es2021-ch6-p6.20"]["footnotes"]


def test_paragraph_6_22_does_not_carry_footnote_6_or_the_page_head(split):
    w = split["es2021-ch6-p6.22"]["snapshot"]["wording"]
    assert "QCI conducted a pilot study" not in w
    assert "Process Reforms: Enabling" not in w
    assert "It is not uncommon to see stocks being over-subscribed" in w  # the sentence joins across the page


def test_a_text_only_splitter_puts_footnote_6_inside_6_22(doc):
    chunk = next(c for c in loci.naive(doc) if c["label"] == "¶6.22")
    assert "stocks being QCI conducted a pilot study as a part of World Bank Technical Assessment" in chunk["text"]
    assert "Process Reforms: Enabling decision-making under uncertainty 189" in chunk["text"]


# --- finding 3: a paragraph runs across a page -------------------------------------

def test_6_22_spans_pages_188_and_189(split):
    p = split["es2021-ch6-p6.22"]
    assert p["printed_pages"] == [188, 189]
    assert p["snapshot"]["locus"] == "¶6.22, printed pp. 188–189"


def test_a_text_only_splitter_gives_6_22_one_page(doc):
    chunk = next(c for c in loci.naive(doc) if c["label"] == "¶6.22")
    assert chunk["page"] == 188  # and nothing records that it goes on to 189


def test_section_heading_c_is_a_locus_of_its_own_on_188(split):
    h = split["es2021-ch6-h188c"]
    assert h["kind"] == "heading"
    assert h["snapshot"]["wording"] == "(c) Discretion is questioned with the benefit of hindsight"
    assert h["printed_pages"] == [188]


# --- the record ---------------------------------------------------------------------

def test_every_snapshot_hash_matches_its_words(split):
    for l in split.values():
        s = l["snapshot"]
        assert hashlib.sha256(s["wording"].encode("utf-8")).hexdigest() == s["wording_sha256"]


def test_snapshots_match_the_v1_3_schema(split):
    jsonschema = pytest.importorskip("jsonschema")
    with open(os.path.join(ROOT, "schema", "snapshot.schema.json"), encoding="utf-8") as f:
        schema = json.load(f)
    for l in split.values():
        jsonschema.validate(l["snapshot"], schema)


def test_loci_match_the_locus_schema(split):
    jsonschema = pytest.importorskip("jsonschema")
    referencing = pytest.importorskip("referencing")
    with open(os.path.join(ROOT, "schema", "locus.schema.json"), encoding="utf-8") as f:
        schema = json.load(f)
    with open(os.path.join(ROOT, "schema", "snapshot.schema.json"), encoding="utf-8") as f:
        snap = json.load(f)
    registry = referencing.Registry().with_resource(snap["$id"], referencing.Resource.from_contents(snap))
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    for l in split.values():
        validator.validate(l)


def test_the_committed_loci_are_what_the_tool_makes():
    out = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "loci.py"), os.path.join(EX, "lines.json"),
                          "--read-on", "2026-10-20"], capture_output=True, text=True, check=True).stdout
    with open(os.path.join(EX, "loci.jsonl"), encoding="utf-8") as f:
        assert f.read() == out


def test_figure_ticks_are_not_taken_for_footnote_numbers():
    """A short line of digits counts as a footnote number only if the page's body carries that marker."""
    page = {"printed_page": 1, "lines": [
        {"y": 100, "h": 15.77, "text": "6.1 Body text with a marker²"},
        {"y": 400, "h": 9.0, "text": "100"},
        {"y": 700, "h": 13.14, "text": "The footnote."},
        {"y": 701, "h": 7.66, "text": "2"}]}
    kinds = [k for k, _ in loci.classify(page, 15.77)]
    assert kinds == ["body", "body", "footnote", "footnote-number"]


# --- pdflines -------------------------------------------------------------------------

def test_pdflines_keeps_markers_and_drops_control_characters():
    html = ('<doc><page><flow><block><line yMin="10" yMax="25.77">'
            '<word yMin="10" yMax="25.77">a</word><word yMin="10" yMax="25.77">study</word>'
            '<word yMin="11" yMax="20.2">6</word></line>'
            '<line yMin="700" yMax="707.66"><word yMin="700" yMax="707.66">6\x07</word></line>'
            '</block></flow></page></doc>')
    out = pdflines.parse(html, 188)["pages"][0]
    assert out["printed_page"] == 188
    assert out["lines"][0]["text"] == "a study⁶"
    assert out["lines"][1]["text"] == "6"
