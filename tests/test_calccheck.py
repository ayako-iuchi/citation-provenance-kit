"""Tests for tools/calccheck.py (kit v1.11).

Run: python3 -m pytest tests
"""
import datetime as dt
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import calccheck as cc  # noqa: E402
import statuslog  # noqa: E402

COMPUTED = os.path.join(ROOT, "register", "computed.jsonl")
STATUS = os.path.join(ROOT, "register", "status_log.jsonl")
TOOL = os.path.join(ROOT, "tools", "calccheck.py")


def run(*args):
    return subprocess.run([sys.executable, TOOL, *args], capture_output=True, text=True)


def rec(**over):
    r = {
        "id": "t-1", "shown": "about 1.6 per cent", "where": "test",
        "inputs": [{"name": "a", "value": 78, "grade": "A"},
                   {"name": "b", "value": 4786, "grade": "A"}],
        "op": {"kind": "divide", "args": ["a", "b"]},
        "display": {"as": "percent", "decimals": 1, "value": "1.6"},
        "operator": "author", "grade_shown": None,
        "recorded_on": "2026-10-23", "recorded_by": "test",
    }
    r.update(over)
    return r


def write(tmp_path, records, name="c.jsonl"):
    p = tmp_path / name
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    return str(p)


# --- the register ----------------------------------------------------------------

def by_id(results, i):
    hits = [r for r in results if r["id"] == i]
    assert len(hits) == 1
    return hits[0]


def test_register_reads_and_has_no_problems():
    records = cc.load(COMPUTED)
    assert cc.check_log(records) == []
    for r in records:
        statuslog.load(STATUS)  # the status log it refers to reads too
        assert r["recorded_by"]


def test_register_every_value_recomputes():
    """Every value in the series' own register is arithmetically right.
    The flags are what recomputing does not find."""
    status = statuslog.load(STATUS)
    results = [cc.check(r, status, "2026-10-23") for r in cc.load(COMPUTED)]
    assert all(r["verdict"] == "recomputes" for r in results)


def test_register_the_series_findings():
    status = statuslog.load(STATUS)
    res = [cc.check(r, status, "2026-10-23") for r in cc.load(COMPUTED)]
    may = by_id(res, "2026-10-23-03")          # "May 2027 [A]" in the domain paper
    assert "grade-borrowed" in may["flags"]
    assert may["detail"]["if_pending"] == {"period": "2026-11"}
    assert may["detail"]["robust"]            # 13 or 14 November: May either way
    marked = by_id(res, "2026-10-23-04")       # the status log marks it
    assert "grade-borrowed" not in marked["flags"]
    readme18 = by_id(res, "2026-10-23-06")     # entry #62
    assert "sensitive" in readme18["flags"]
    assert readme18["detail"]["over_inputs"] == ["17", "18"]
    days = by_id(res, "2026-10-23-08")
    assert days["computed"] == "79" and days["detail"]["over_inputs"] == ["78", "79"]
    assert by_id(res, "2026-10-23-09")["computed"] == "23:36"
    assert "grade-borrowed" in by_id(res, "2026-10-23-10")["flags"]   # the status log's own month
    assert "operator-unknown" in by_id(res, "2026-10-23-02")["flags"]
    assert by_id(res, "2026-10-23-01")["operator"] == "source"


# The register as released in kit v1.11: these lines stand as written. Later
# records are appended after them; a correction is a new record that supersedes.
V1_11_LINES = 10
V1_11_SHA256 = "4a8a4b90b067cd4e7216e630a048559748f3e5d2b7f178030abeb305af4990b3"


def test_register_is_append_only_against_v1_11():
    import hashlib
    with open(COMPUTED, "rb") as f:
        lines = f.read().split(b"\n")[:V1_11_LINES]
    assert hashlib.sha256(b"\n".join(lines)).hexdigest() == V1_11_SHA256


# --- operations --------------------------------------------------------------------

def test_add_months_keeps_the_day_or_takes_the_last():
    assert cc.add_months(dt.date(2025, 11, 13), 18) == dt.date(2027, 5, 13)
    assert cc.add_months(dt.date(2025, 11, 14), 18) == dt.date(2027, 5, 14)
    assert cc.add_months(dt.date(2025, 11, 13), 12) == dt.date(2026, 11, 13)
    assert cc.add_months(dt.date(2026, 8, 31), 6) == dt.date(2027, 2, 28)
    assert cc.add_months(dt.date(2027, 8, 31), 6) == dt.date(2028, 2, 29)


def test_divide_and_rounding_half_up():
    assert cc.render(cc.apply("divide", 78, 4786), {"as": "percent", "decimals": 2}) == "1.63"
    assert cc.render(cc.apply("divide", 78, 4787), {"as": "percent", "decimals": 2}) == "1.63"
    assert cc.render(cc.apply("divide", 1, 8), {"as": "decimal", "decimals": 2}) == "0.13"  # 0.125
    assert cc.render(cc.apply("divide", 1, 40), {"as": "percent", "decimals": 1}) == "2.5"


def test_days_minutes_count():
    assert cc.apply("days_between", "2026-07-26", "2026-10-13") == 79
    assert cc.apply("days_between", "2026-07-24", "2026-10-13") == 81
    assert cc.apply("minutes_between", "2026-10-21T13:46", "2026-10-22T13:22") == 1416
    assert cc.render(cc.apply("minutes_between", "2026-10-21T13:46", "2026-10-22T13:22"),
                     {"as": "hours_minutes"}) == "23:36"
    assert cc.apply("count", ["#1", "#2", "#2", "#3"], ["#3"]) == 2


def test_division_by_zero_and_bad_types_are_malformed():
    with pytest.raises(cc.Malformed):
        cc.apply("divide", 1, 0)
    with pytest.raises(cc.Malformed):
        cc.apply("add_months", "13 Nov 2025", 18)
    with pytest.raises(cc.Malformed):
        cc.apply("add_months", "2025-11-13", 1.5)
    with pytest.raises(cc.Malformed):
        cc.apply("divide", True, 2)
    with pytest.raises(cc.Malformed):
        cc.render(dt.date(2027, 5, 13), {"as": "percent"})


def test_no_eval():
    src = open(os.path.join(ROOT, "tools", "calccheck.py"), encoding="utf-8").read()
    assert "eval(" not in src.replace("without eval()", "")


# --- verdicts and flags ------------------------------------------------------------

def test_differs():
    r = cc.check(rec(display={"as": "percent", "decimals": 1, "value": "1.7"}))
    assert r["verdict"] == "differs" and r["computed"] == "1.6"


def test_grade_borrowed_only_when_someone_else_computed_and_A_is_shown_unmarked():
    assert "grade-borrowed" in cc.check(rec(grade_shown="[A]"))["flags"]
    assert "grade-borrowed" in cc.check(rec(operator="assistant", grade_shown="A — G.S.R. 843(E)"))["flags"]
    assert "grade-borrowed" not in cc.check(rec(operator="source", grade_shown="[A]"))["flags"]
    assert "grade-borrowed" not in cc.check(rec(grade_shown="[figure: A | attribution: D]"))["flags"]
    assert "grade-borrowed" not in cc.check(rec(grade_shown="［数値: A｜帰属: D］"))["flags"]
    assert "grade-borrowed" not in cc.check(rec(grade_shown="[A, derived by the author]"))["flags"]
    assert "grade-borrowed" in cc.check(rec(grade_shown="[Ａ]"))["flags"]          # full width
    assert "grade-borrowed" in cc.check(rec(grade_shown="All rows Grade A."))["flags"]
    assert "grade-borrowed" in cc.check(rec(grade_shown="A text / B source"))["flags"]
    # a mark in the value itself counts
    assert "grade-borrowed" not in cc.check(rec(shown="May 2027 (author's arithmetic)", grade_shown="A"))["flags"]
    assert "grade-borrowed" not in cc.check(rec(grade_shown="［A。月は著者の計算］"))["flags"]
    assert "grade-borrowed" not in cc.check(rec(grade_shown="[C]"))["flags"]
    assert "grade-borrowed" not in cc.check(rec(grade_shown=None))["flags"]
    # an A that is not a grade
    for g in ("Annex", "Annex A", "[D; Exhibit A-6]", "[C (see Appendix A)]", "[A1]"):
        assert "grade-borrowed" not in cc.check(rec(grade_shown=g))["flags"], g


def test_operator_unknown_and_claims_disagree():
    r = cc.check(rec(operator="unknown", operator_claims=[
        {"by": "paper 1", "says": "source"}, {"by": "paper 2", "says": "author"}]))
    assert {"operator-unknown", "claims-disagree"} <= set(r["flags"])
    r = cc.check(rec(operator_claims=[{"by": "x", "says": "author"}, {"by": "y", "says": "author"}]))
    assert "claims-disagree" not in r["flags"]
    # one claim against the record's own operator
    r = cc.check(rec(operator_claims=[{"by": "x", "says": "source"}]))
    assert "claims-disagree" in r["flags"]


def test_range_and_alternatives_robust_or_sensitive():
    robust = rec(inputs=[{"name": "a", "value": 78}, {"name": "b", "value": 4786, "range": [4786, 4787]}])
    assert cc.check(robust)["detail"]["robust"]
    sens = rec(inputs=[{"name": "a", "value": 78}, {"name": "b", "value": 4786, "range": [4000, 4787]}])
    r = cc.check(sens)
    assert "sensitive" in r["flags"] and r["detail"]["over_inputs"] == ["1.6", "2.0"]
    day = rec(inputs=[{"name": "d", "value": "2025-11-13", "alternatives": ["2025-11-14"]},
                      {"name": "m", "value": 18}],
              op={"kind": "add_months", "args": ["d", "m"]},
              display={"as": "day", "value": "2027-05-13"})
    assert "sensitive" in cc.check(day)["flags"]          # a day is sensitive
    month = dict(day, display={"as": "month", "value": "2027-05"})
    assert "sensitive" not in cc.check(month)["flags"]    # the month is not


def test_month_boundary_makes_month_sensitive():
    r = rec(inputs=[{"name": "d", "value": "2025-11-30", "alternatives": ["2025-12-01"]},
                    {"name": "m", "value": 18}],
            op={"kind": "add_months", "args": ["d", "m"]},
            display={"as": "month", "value": "2027-05"})
    assert "sensitive" in cc.check(r)["flags"]


def test_if_pending():
    r = rec(inputs=[{"name": "d", "value": "2025-11-13"},
                    {"name": "m", "value": 18, "pending": {"value": 12, "note": "consultation"}}],
            op={"kind": "add_months", "args": ["d", "m"]},
            display={"as": "month", "value": "2027-05"})
    assert cc.check(r)["detail"]["if_pending"] == {"m": "2026-11"}
    same = rec(inputs=[{"name": "a", "value": 78}, {"name": "b", "value": 4786, "pending": 4786.5}])
    assert "if-pending" not in cc.check(same)["flags"]


def test_status_expired_and_unrecorded():
    status = statuslog.load(STATUS)
    subj = {"subject": "India — DPDP Rules 2025, Rules 3, 5–16, 22, 23", "component": "commencement"}
    r = rec(inputs=[{"name": "d", "value": "2025-11-13"}, {"name": "m", "value": 18, "status": subj}],
            op={"kind": "add_months", "args": ["d", "m"]}, display={"as": "month", "value": "2027-05"})
    assert "input-expired" not in cc.check(r, status, "2026-11-10")["flags"]
    assert "input-expired" in cc.check(r, status, "2026-11-11")["flags"]
    gone = dict(r, inputs=[{"name": "d", "value": "2025-11-13"},
                           {"name": "m", "value": 18, "status": {"subject": "nothing", "component": "commencement"}}])
    assert "input-unrecorded" in cc.check(gone, status, "2026-10-23")["flags"]


# --- malformed input and the command line ------------------------------------------

@pytest.mark.parametrize("bad", [
    {"operator": "me"},
    {"op": {"kind": "sqrt", "args": ["a"]}},
    {"op": {"kind": "divide", "args": ["a"]}},
    {"op": {"kind": "divide", "args": ["a", "c"]}},
    {"display": {"as": "percent"}},
    {"display": {"as": "weeks", "value": "1"}},
    {"inputs": []},
    {"inputs": [{"name": "a", "value": 1}, {"name": "a", "value": 2}]},
    {"inputs": [{"name": "a", "value": 1, "rnage": [1, 2]}, {"name": "b", "value": 2}]},
    {"inputs": [{"name": "a", "value": 1, "range": [1]}, {"name": "b", "value": 2}]},
    {"operator_claims": [{"by": "x", "says": "maybe"}]},
    {"recorded_on": "23 Oct 2026"},
    {"recorded_on": "20261023"},
    {"colour": "red"},
    {"shown": ["1.6"]},
    {"grade_shown": 1},
    {"operator_claims": 3},
    {"display": {"as": "percent", "decimals": 40, "value": "1.6"}},
    {"display": {"as": "percent", "decimals": -1, "value": "1.6"}},
    {"display": {"as": "percent", "decimals": 1, "value": 1.6}},
    {"inputs": [{"name": "a", "value": "NaN"}, {"name": "b", "value": 4786}]},
    {"inputs": [{"name": "a", "value": "Infinity"}, {"name": "b", "value": 4786}]},
    {"inputs": [{"name": "a", "value": 1e30}, {"name": "b", "value": 1}]},
    {"inputs": [{"name": "a", "value": 78, "alternatives": "47"}, {"name": "b", "value": 4786}]},
    {"inputs": [{"name": "a", "value": 78, "pending": {"note": "x"}}, {"name": "b", "value": 4786}]},
    {"inputs": [{"name": "a", "value": [1, 2]}, {"name": "b", "value": 4786}]},
    {"inputs": [{"name": "a", "value": "2025-11-13T10:00+09:00"}, {"name": "b", "value": "2025-11-14T10:00"}],
     "op": {"kind": "minutes_between", "args": ["a", "b"]}, "display": {"as": "integer", "value": "1"}},
    {"inputs": [{"name": "a", "value": "2025-W46-4"}, {"name": "b", "value": 18}],
     "op": {"kind": "add_months", "args": ["a", "b"]}, "display": {"as": "month", "value": "2027-05"}},
])
def test_malformed_records(tmp_path, bad):
    p = write(tmp_path, [rec(**bad)])
    assert run("--log", p).returncode == 2


def test_cli_exit_codes(tmp_path):
    ok = write(tmp_path, [rec()], "ok.jsonl")
    assert run("--log", ok).returncode == 0
    flagged = write(tmp_path, [rec(grade_shown="[A]")], "f.jsonl")
    assert run("--log", flagged).returncode == 1
    p = tmp_path / "notjson.jsonl"
    p.write_text("{nope\n", encoding="utf-8")
    assert run("--log", str(p)).returncode == 2
    assert run("--log", str(tmp_path / "missing.jsonl")).returncode == 2
    assert run("--log", ok, "--status", STATUS, "--on", "23/10/2026").returncode == 2


def test_cli_supersedes(tmp_path):
    a = rec(id="x-1", display={"as": "percent", "decimals": 1, "value": "1.7"})
    b = rec(id="x-2", supersedes="x-1")
    p = write(tmp_path, [a, b])
    out = run("--log", p, "--json")
    assert out.returncode == 0
    assert [r["id"] for r in json.loads(out.stdout)] == ["x-2"]
    assert run("--log", p, "--all").returncode == 1
    bad = write(tmp_path, [b], "bad.jsonl")
    assert run("--log", bad).returncode == 2


def test_cli_status_needs_on_and_good_lines(tmp_path):
    ok = write(tmp_path, [rec()], "ok.jsonl")
    assert run("--log", ok, "--status", STATUS).returncode == 2
    bad = tmp_path / "status.jsonl"
    bad.write_text(json.dumps({"id": "x", "component": "commencement", "recorded_on": "2026-10-10"}) + "\n", encoding="utf-8")
    assert run("--log", ok, "--status", str(bad), "--on", "2026-10-23").returncode == 2


def test_cli_superseded_twice(tmp_path):
    a = rec(id="x-1")
    p = write(tmp_path, [a, rec(id="x-2", supersedes="x-1"), rec(id="x-3", supersedes="x-1")])
    assert run("--log", p).returncode == 2


def test_cli_on_the_register():
    out = run("--log", COMPUTED, "--status", STATUS, "--on", "2026-10-23")
    assert out.returncode == 1
    assert "grade-borrowed" in out.stdout and "if period takes its pending value: 2026-11" in out.stdout


def test_evidence_matches_the_tool():
    """evidence/calccheck_2026-10-23.txt is what the README's command prints."""
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    assert "--status register/status_log.jsonl --on 2026-10-23 --all" in readme
    path = os.path.join(ROOT, "evidence", "calccheck_2026-10-23.txt")
    out = run("--log", COMPUTED, "--status", STATUS, "--on", "2026-10-23", "--all")
    with open(path, encoding="utf-8") as f:
        assert f.read().rstrip("\n") == out.stdout.rstrip("\n")


def test_register_matches_schema():
    jsonschema = pytest.importorskip("jsonschema")
    with open(os.path.join(ROOT, "schema", "computed.schema.json"), encoding="utf-8") as f:
        schema = json.load(f)
    for r in cc.load(COMPUTED):
        jsonschema.validate(r, schema)
