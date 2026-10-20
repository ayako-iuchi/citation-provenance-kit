"""Tests for tools/retrieve.py and tools/depaudit.py (kit v1.4).

Run: python3 -m pytest tests
"""
import copy
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import depaudit  # noqa: E402
import retrieve  # noqa: E402
import statuslog  # noqa: E402

EX = os.path.join(ROOT, "examples", "es2021_ch6")
ON = "2026-10-20"


@pytest.fixture(scope="module")
def loci():
    return depaudit.load_jsonl(os.path.join(EX, "loci.jsonl"))


@pytest.fixture(scope="module")
def deps():
    return depaudit.load_jsonl(os.path.join(EX, "dependencies.jsonl"))


@pytest.fixture(scope="module")
def log():
    return statuslog.load(os.path.join(ROOT, "register", "status_log.jsonl"))


# --- retrieval proposes ---------------------------------------------------------------

def test_the_contract_question_retrieves_6_32_first(loci):
    hits = retrieve.BM25(loci).search("How many days does it take to resolve a commercial contract in India?")
    assert hits[0]["id"] == "es2021-ch6-p6.32"


def test_the_index_reads_only_words(loci):
    """Status and dependencies are not in the index: adding them to a locus changes no score."""
    q = "Why does L1 persist in Indian public procurement?"
    before = retrieve.BM25(loci).search(q, k=5)
    dressed = copy.deepcopy(loci)
    for l in dressed:
        l["status"] = "Discontinued, Doing Business"
    assert retrieve.BM25(dressed).search(q, k=5) == before


def test_no_stemming_persist_does_not_match_persists():
    assert "persist" not in retrieve.tokens("The L1 system persists")


# --- finding 2: a name match misses in both directions -------------------------------

def test_name_match_on_doing_business_misses_6_32(loci):
    assert depaudit.suggest(loci, "Doing Business") == ["es2021-ch6-p6.5"]  # ¶6.32 prints "Buisness"


def test_name_match_on_business_judgment_misses_6_27(loci):
    assert depaudit.suggest(loci, "Business Judgment") == []  # ¶6.27 prints "Buisness Judgment Rule"
    assert depaudit.suggest(loci, "Buisness") == ["es2021-ch6-p6.27", "es2021-ch6-p6.32"]


def test_an_unknown_locus_is_an_error(loci, deps, log):
    with pytest.raises(KeyError):
        depaudit.audit("es2021-ch6-p9.99", loci, deps, log, ON)


def test_name_match_on_world_bank_flags_6_20(loci, deps):
    assert "es2021-ch6-p6.20" in depaudit.suggest(loci, "World Bank")
    assert not any(d["locus"] in ("es2021-ch6-p6.20", "es2021-ch6-fn6") and d.get("status_subject") ==
                   "World Bank — Doing Business report" for d in deps)


def test_recorded_edges_reach_doing_business_from_6_5_and_6_32_only(deps):
    reach = sorted(d["locus"] for d in deps if d.get("status_subject") == "World Bank — Doing Business report")
    assert reach == ["es2021-ch6-p6.32", "es2021-ch6-p6.5"]


# --- the check after retrieval ----------------------------------------------------------

def test_6_32_reaches_a_discontinued_report_with_its_status_attached(loci, deps, log):
    row = depaudit.audit("es2021-ch6-p6.32", loci, deps, log, ON)
    db = next(d for d in row["dependencies"] if d["cites"] == "World Bank, Doing Business 2020")
    assert db["status"]["status"] == "no-expiry-stated"
    assert db["status"]["value"].startswith("Discontinued")
    assert db["status"]["assertion"] == "2026-10-20-01"
    assert db["status"]["expires_on"] is None
    wjp = next(d for d in row["dependencies"] if d["cites"].startswith("World Justice Project"))
    assert wjp["status"]["status"] == "not-tracked"


def test_the_l1_loci_do_not_reach_it(loci, deps, log):
    for lid in ("es2021-ch6-p6.19", "es2021-ch6-p6.20", "es2021-ch6-p6.21", "es2021-ch6-h188c", "es2021-ch6-p6.27"):
        row = depaudit.audit(lid, loci, deps, log, ON)
        assert row["depth"] == 1
        assert all(d["status"]["status"] == "not-tracked" for d in row["dependencies"])


def test_a_footnote_travels_with_its_anchor(loci, deps, log):
    row = depaudit.audit("es2021-ch6-p6.20", loci, deps, log, ON)
    via = [d for d in row["dependencies"] if d["via"] == "es2021-ch6-fn6"]
    assert len(via) == 1 and via[0]["cites"].startswith("World Bank Technical Assessment")


def test_no_record_is_not_the_same_as_names_no_work(loci, deps, log):
    assert depaudit.audit("es2021-ch6-p6.18", loci, deps, log, ON)["result"].startswith("not audited")
    assert depaudit.audit("es2021-ch6-p6.21", loci, deps, log, ON)["result"] == "audited at depth 1: names no work"


def test_depth_two_is_named_as_unknown(loci, deps, log):
    row = depaudit.audit("es2021-ch6-p6.19", loci, deps, log, ON)
    assert row["unknowns"] == ["what Government of India, General Financial Rules itself rests on (depth 2, not audited)"]


def test_an_edited_snapshot_is_caught(loci, deps, log):
    tampered = copy.deepcopy(loci)
    s = next(l for l in tampered if l["id"] == "es2021-ch6-p6.21")["snapshot"]
    s["wording"] = s["wording"].replace("regulatory default problem", "price preference")
    assert depaudit.audit("es2021-ch6-p6.21", tampered, deps, log, ON)["wording_sha256_ok"] is False


def test_a_quotation_is_checked_against_the_pinned_words(loci, deps, log):
    ok = depaudit.audit("es2021-ch6-p6.21", loci, deps, log, ON,
                        quote="The L1 system persists because of the regulatory default problem.")
    bad = depaudit.audit("es2021-ch6-p6.21", loci, deps, log, ON, quote="L1 persists because of price preference.")
    assert ok["quote_found"] is True and bad["quote_found"] is False


# --- the records ----------------------------------------------------------------------------

def test_every_edge_names_a_locus_that_exists(loci, deps):
    ids = {l["id"] for l in loci}
    assert all(d["locus"] in ids for d in deps)


def test_edges_match_the_schema(deps):
    jsonschema = pytest.importorskip("jsonschema")
    with open(os.path.join(ROOT, "schema", "dependency.schema.json"), encoding="utf-8") as f:
        schema = json.load(f)
    for d in deps:
        jsonschema.validate(d, schema)


def test_edge_ids_are_unique(deps):
    assert len({d["id"] for d in deps}) == len(deps)
