"""Tests for tools/nulleval.py (kit v1.6)."""
import json
import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import nulleval  # noqa: E402

ITEMS = os.path.join(ROOT, "evals", "null", "items.jsonl")
V = {"kind": "value", "accept": [["april", "2023"]]}
NE = {"kind": "empty", "empty": "not-established"}


@pytest.mark.parametrize("gold,ans,outcome", [
    (V, {"answer": "Financial years from 1 April 2023"}, "value-correct"),
    (V, {"answer": "1 April 2022"}, "value-wrong"),
    (V, {"answer": None, "empty": "not-established"}, "blanked"),
    (V, {"answer": "Not stated."}, "blanked"),
    (NE, {"answer": "G.S.R. 235(E)"}, "filled"),
    (NE, {"answer": None, "empty": "not-established"}, "empty-correct"),
    (NE, {"answer": None, "empty": "expired"}, "empty-kind"),
    (NE, {"answer": "The evidence does not say."}, "empty-kind"),
    (NE, None, "empty-kind"),
])
def test_outcomes(gold, ans, outcome):
    assert nulleval.score_slot(gold, ans) == outcome


def test_unspecified_empty_is_never_correct():
    for kind in ("not-established", "expired", "no-record"):
        assert nulleval.score_slot({"kind": "empty", "empty": kind}, {"answer": ""}) == "empty-kind"


def test_none_is_a_value_not_an_empty():
    # "None" can be the right value ("cites nothing"); it is not read as an empty.
    gold = {"kind": "value", "accept": ["none", "nothing"]}
    assert nulleval.score_slot(gold, {"answer": "None"}) == "value-correct"


def test_items_validate():
    jsonschema = pytest.importorskip("jsonschema")
    with open(os.path.join(ROOT, "schema", "null_item.schema.json"), encoding="utf-8") as f:
        schema = json.load(f)
    for item in nulleval.load_items(ITEMS):
        jsonschema.validate(item, schema)
        assert "__" not in json.dumps(item), "placeholder left in items"


def test_items_mix_values_and_each_kind_of_empty():
    golds = [s["gold"] for i in nulleval.load_items(ITEMS) for s in i["slots"]]
    values = sum(1 for g in golds if g["kind"] == "value")
    kinds = {g["empty"] for g in golds if g["kind"] == "empty"}
    assert values and len(golds) - values
    assert kinds == {"not-established", "expired", "no-record"}


@pytest.mark.parametrize("mode", ["fill", "empty"])
def test_both_baselines_fail(mode):
    items = nulleval.load_items(ITEMS)
    r = nulleval.score(items, nulleval.baseline(items, mode)["answers"])
    c = r["counts"]
    if mode == "fill":
        assert c["filled"] == r["gold_empties"] and c["empty-correct"] == 0
    else:
        assert c["blanked"] == r["gold_values"] and c["value-correct"] == 0


def test_empty_answers_count_against_values_and_kinds_separately():
    items = nulleval.load_items(ITEMS)
    r = nulleval.score(items, {})
    assert r["counts"]["blanked"] == r["gold_values"]
    assert r["counts"]["empty-kind"] == r["gold_empties"]


def test_cli(tmp_path, capsys):
    p = tmp_path / "a.json"
    p.write_text(json.dumps({"model": "m", "answers": {}}), encoding="utf-8")
    assert nulleval.main([ITEMS, str(p), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["model"] == "m"
    assert nulleval.main([ITEMS, str(tmp_path / "missing.json")]) == 2


# --- prose is read, not guessed (2026-10-20) ---------------------------------

PROSE = {"answer": "Not stated in the evidence. From memory: G.S.R. 999(E)."}


def test_prose_refusal_is_unread_until_read():
    assert nulleval.score_slot(NE, PROSE) == "unread"
    assert nulleval.score_slot(V, {"answer": "Unknown. The excerpt does not say."}) == "unread"


def test_readings_decide_prose():
    assert nulleval.score_slot(NE, PROSE, {"read_as": "empty-then-value"}) == "filled"
    assert nulleval.score_slot(NE, PROSE, {"read_as": "empty", "kind": "not-established"}) == "empty-correct"
    assert nulleval.score_slot(NE, PROSE, {"read_as": "empty"}) == "empty-kind"
    gold = {"kind": "value", "accept": ["nothing"]}
    assert nulleval.score_slot(gold, {"answer": "None. It cites nothing."}, {"read_as": "value"}) == "value-correct"


def test_short_values_are_not_prose_refusals():
    assert nulleval.score_slot(V, {"answer": "Financial years from 1 April 2023"}) == "value-correct"
