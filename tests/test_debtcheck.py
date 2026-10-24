"""Tests for tools/debtcheck.py and tools/elapsed.py (kit v1.13), and for the durations of the series log."""
import json
import os
import shlex
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import catchlog  # noqa: E402
import debtcheck  # noqa: E402
import elapsed  # noqa: E402

REGISTER = os.path.join(ROOT, "register", "deferred.jsonl")
EVIDENCE = os.path.join(ROOT, "evidence", "debtcheck_2026-10-24.txt")
TIMES = os.path.join(ROOT, "evidence", "git_times_2026-10-24.tsv")
THROUGH_78 = os.path.join(ROOT, "examples", "series_log", "through_78.csv")


def D(i, **kw):
    r = {"id": i, "kind": "deferral", "log": "log #1", "document": "Paper", "where": "§1", "fix_in": "next edition",
         "condition": None, "found_on": "2026-10-01", "recorded_on": "2026-10-01", "decided_by": "author", "note": ""}
    r.update(kw)
    return r


def P(i, pays, on="2026-10-05", inn="v2", **kw):
    r = {"id": i, "kind": "payment", "pays": pays, "paid_on": on, "paid_in": inn, "note": ""}
    r.update(kw)
    return r


def E(i, ed="v2", on="2026-10-05", doc="Paper", **kw):
    r = {"id": i, "kind": "edition", "document": doc, "edition": ed, "published_on": on, "note": ""}
    r.update(kw)
    return r


def W(i, of, on="2026-10-05", **kw):
    r = {"id": i, "kind": "withdrawal", "withdraws": of, "withdrawn_on": on, "reason": "condition not met", "note": ""}
    r.update(kw)
    return r


def write(tmp_path, recs, name="d.jsonl"):
    p = tmp_path / name
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
    return str(p)


# --- the kit's register ------------------------------------------------------

def test_register_is_valid_and_matches_schema_fields():
    recs = debtcheck.load(REGISTER)
    assert debtcheck.check(recs) == []
    schema = json.load(open(os.path.join(ROOT, "schema", "deferred.schema.json"), encoding="utf-8"))
    by_kind = {s["properties"]["kind"]["const"]: set(s["required"]) for s in schema["oneOf"]}
    assert by_kind == debtcheck.FIELDS


def test_register_counts():
    rep = debtcheck.report(debtcheck.load(REGISTER), "2026-10-24")
    mp = rep["What Breaks in a Citation (method paper)"]
    assert (mp["open"], mp["conditional"], mp["paid"]) == (16, 2, 0)
    assert mp["oldest"]["log"] == "log #45" and mp["oldest"]["basis"] == "recorded" and mp["oldest"]["age_days"] == 11
    kit = rep["citation-provenance-kit"]
    assert (kit["paid"], kit["open"]) == (5, 0) and kit["latest_edition"]["edition"] == "v1.12"
    assert all(not r["overdue"] for r in rep.values())


def test_register_names_every_log_number():
    for r in debtcheck.load(REGISTER):
        for k, v in r.items():
            if isinstance(v, str) and "#" in v:
                import re
                for m in re.finditer(r"(\S*)\s?#(\d+)", v):
                    assert m.group(1).endswith("log") or m.group(1) == "log", (r["id"], v)


def _sections(text):
    return [b.strip("\n") for b in text.split("\n\n$ ")[1:]]


def test_evidence_reproduces():
    stored = open(EVIDENCE, encoding="utf-8").read()
    for block in _sections(stored):
        cmd, _, want = block.partition("\n")
        r = subprocess.run(shlex.split(cmd), cwd=ROOT, capture_output=True, text=True)
        got = r.stdout.rstrip("\n") + (f"\n[exit {r.returncode}]" if r.returncode else "")
        assert got == want.rstrip("\n"), cmd


# --- debtcheck ---------------------------------------------------------------

def test_open_paid_and_age(tmp_path):
    p = write(tmp_path, [D("a"), D("b", found_on=None, recorded_on="2026-10-03", condition="if confirmed"), P("c", "a")])
    rep = debtcheck.report(debtcheck.load(p), "2026-10-10")["Paper"]
    assert (rep["open"], rep["conditional"], rep["paid"]) == (1, 1, 1)
    assert rep["oldest"] == {"id": "b", "log": "log #1", "date": "2026-10-03", "basis": "recorded", "age_days": 7}
    assert rep["found_date_not_recorded"] == ["log #1"]


def test_as_of_an_earlier_day_ignores_later_lines(tmp_path):
    p = write(tmp_path, [D("a"), P("c", "a", on="2026-10-05"), D("b", recorded_on="2026-10-08", found_on="2026-10-08")])
    rep = debtcheck.report(debtcheck.load(p), "2026-10-04")["Paper"]
    assert (rep["open"], rep["paid"]) == (1, 0)


def test_next_edition_out_without_it_is_overdue(tmp_path):
    p = write(tmp_path, [D("a"), E("e", on="2026-10-05")])
    recs = debtcheck.load(p)
    assert debtcheck.report(recs, "2026-10-04")["Paper"]["overdue"] == []
    over = debtcheck.report(recs, "2026-10-06")["Paper"]["overdue"]
    assert [o["id"] for o in over] == ["a"]
    assert debtcheck.main([p, "--on", "2026-10-06"]) == 1


def test_edition_on_the_day_recorded_is_not_the_next(tmp_path):
    # Found in the edition published that day: the next edition is a later one.
    p = write(tmp_path, [E("e", ed="v1", on="2026-10-01"), D("a")])
    assert debtcheck.report(debtcheck.load(p), "2026-10-10")["Paper"]["overdue"] == []


def test_named_edition(tmp_path):
    p = write(tmp_path, [D("a", fix_in="v3"), E("e2", ed="v2", on="2026-10-05"), E("e3", ed="v3", on="2026-10-07")])
    recs = debtcheck.load(p)
    assert debtcheck.report(recs, "2026-10-06")["Paper"]["overdue"] == []
    assert [o["edition"] for o in debtcheck.report(recs, "2026-10-08")["Paper"]["overdue"]] == ["v3"]


def test_paid_is_not_overdue(tmp_path):
    p = write(tmp_path, [D("a"), E("e", on="2026-10-05"), P("c", "a", on="2026-10-05")])
    assert debtcheck.report(debtcheck.load(p), "2026-10-06")["Paper"]["overdue"] == []


def test_other_documents_editions_do_not_count(tmp_path):
    p = write(tmp_path, [D("a"), E("e", doc="Other", on="2026-10-05")])
    assert debtcheck.report(debtcheck.load(p), "2026-10-06")["Paper"]["overdue"] == []


@pytest.mark.parametrize("recs,needle", [
    ([D("a"), D("a")], "used twice"),
    ([P("c", "a"), D("a")], "not a deferral recorded earlier"),
    ([D("a"), P("c", "a"), P("d", "a")], "already closed"),
    ([D("a", recorded_on="2026-10-04"), P("c", "a", on="2026-10-03")], "before the deferral"),
    ([D("a", found_on="2026-10-02", recorded_on="2026-10-01")], "after it was recorded"),
    ([E("e"), P("c", "e")], "not a deferral"),
    ([D("a"), P("c", "a", inn="v9")], "not an edition of Paper"),
    ([E("e1"), E("e2"), D("a")], "recorded twice"),
    ([D("a", fix_in="Next edition")], "exactly"),
    ([D("a", fix_in="next edition ")], "exactly"),
    ([D("a", fix_in="次の版")], "exactly"),
    ([D("a", fix_in=" v2")], "spaces"),
    ([D("a", fix_in="next ed.")], "exactly"),
    ([D("a", fix_in="次回の改訂")], "exactly"),
    ([D("a"), E("e", on="2026-10-06"), P("c", "a", on="2026-10-05", inn="v2")], "was published on"),
    ([D("a"), W("w", "a", reason=" ")], "reason"),
    ([D("a"), W("w", "a"), P("c", "a")], "already closed"),
])
def test_check_problems(tmp_path, recs, needle, capsys):
    p = write(tmp_path, recs)
    assert any(needle in x for x in debtcheck.check(debtcheck.load(p)))
    assert debtcheck.main([p, "--check"]) == 1
    assert debtcheck.main([p, "--on", "2026-10-10"]) == 2


@pytest.mark.parametrize("line", [
    "not json", "[1, 2]", json.dumps({"kind": "loan"}),
    json.dumps({**D("a"), "extra": 1}),
    json.dumps({k: v for k, v in D("a").items() if k != "where"}),
    json.dumps(D("a", recorded_on="2026-10-1")), json.dumps(D("a", recorded_on="2026-02-30")),
    json.dumps(D("a", recorded_on=None)), json.dumps(D("a", where=["§1"])), json.dumps(D("a", note=None)),
    "[" * 5000,
    json.dumps(D("a", recorded_on="2026-W40-4")), json.dumps(D("a", recorded_on="20261001")),
    '{"id": "a", "id": "b"}', '{"n": ' + "1" * 5000 + '}',
])
def test_malformed_exits_2(tmp_path, line, capsys):
    p = tmp_path / "bad.jsonl"
    p.write_text(line + "\n", encoding="utf-8")
    assert debtcheck.main([str(p), "--check"]) == 2
    assert "debtcheck:" in capsys.readouterr().err


def test_bad_day_and_missing_file(tmp_path, capsys):
    p = write(tmp_path, [D("a")])
    assert debtcheck.main([p, "--on", "24 Oct"]) == 2
    assert debtcheck.main([str(tmp_path / "none.jsonl"), "--check"]) == 2


def test_json_output(tmp_path, capsys):
    p = write(tmp_path, [D("a")])
    assert debtcheck.main([p, "--on", "2026-10-10", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["documents"]["Paper"]["open"] == 1


# --- elapsed -----------------------------------------------------------------

def test_spans_from_the_stored_times():
    sp = {s["tag"]: s for s in elapsed.spans(elapsed.from_tsv(TIMES))}
    assert sp["v1.12"]["minutes"] == 59 and sp["v1.12"]["first_commit"] == "beb4a7b"
    named = {s["tag"]: s for s in elapsed.spans(elapsed.from_tsv(TIMES), named=True)}
    assert named["v1.12"]["first_commit"] == "db7c95a" and named["v1.12"]["minutes"] == 39
    assert named["v1.6"]["commits"] == 9  # every commit in the span, not only those that name the tag
    assert named["v1.12"]["last_commit"] == "146d887"


@pytest.mark.parametrize("tag,subject,want", [
    ("v1.12", "Kit v1.12: release (23 October 2026)", True),
    ("v1.12", "Kit v1.12 (in preparation): identifiers", True),
    ("v1.1", "Kit v1.12: release", False),
    ("v1.1", "Kit v1.1.1: fix", False),
    ("v1.3", "Merge branch 'kit-v1.3'", False),
    ("v1.1", "Kit v1.1-rc1: candidate", False),
    ("v1.12", "Kit v1.120", False),
    ("v1.12", "README: add Hypothetical Technical Blog #31", False),
    ("v1.1", "Kit v1.1: reproduction kit", True),
])
def test_names(tag, subject, want):
    assert elapsed.names(tag, subject) is want


def test_named_with_no_commit(tmp_path):
    p = tmp_path / "t.tsv"
    p.write_text("v2\tabc\t2026-10-01T10:00:00+09:00\tREADME only\n", encoding="utf-8")
    sp = elapsed.spans(elapsed.from_tsv(str(p)), named=True)
    assert sp[0]["commits"] == 0
    assert "no commit names this tag" in elapsed.render(sp)


def test_output_says_not_effort(capsys):
    assert elapsed.main(["--from", TIMES]) == 0
    assert capsys.readouterr().out.startswith("Elapsed clock time between commits. Not effort")


@pytest.mark.parametrize("content", ["v1\tabc\n", "v1\tabc\tyesterday\ts\n", "v1\tabc\t2026-10-01T10:00:00\ts\n"])
def test_elapsed_bad_input_exits_2(tmp_path, content, capsys):
    p = tmp_path / "t.tsv"
    p.write_text(content, encoding="utf-8")
    assert elapsed.main(["--from", str(p)]) == 2


def test_from_git(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    env = {**os.environ, "GIT_AUTHOR_NAME": "a", "GIT_AUTHOR_EMAIL": "a@x", "GIT_COMMITTER_NAME": "a", "GIT_COMMITTER_EMAIL": "a@x"}

    def git(*a, when=None):
        e = dict(env)
        if when:
            e["GIT_COMMITTER_DATE"] = e["GIT_AUTHOR_DATE"] = when
        subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, env=e)
    git("init", "-q")
    for i, (when, msg, tag) in enumerate([("2026-10-01T09:00:00+09:00", "Kit v1.0: start", "v1.0"),
                                          ("2026-10-02T09:00:00+09:00", "README: after v1.0", None),
                                          ("2026-10-02T10:00:00+09:00", "Kit v1.1: work", None),
                                          ("2026-10-02T10:45:00+09:00", "Kit v1.1: release", "v1.1")]):
        (repo / "f").write_text(str(i))
        git("add", "f")
        git("commit", "-q", "-m", msg, when=when)
        if tag:
            git("tag", tag)
    sp = {s["tag"]: s for s in elapsed.spans(elapsed.from_git(str(repo)))}
    assert sp["v1.1"]["commits"] == 3 and sp["v1.1"]["minutes"] == 105
    sp = {s["tag"]: s for s in elapsed.spans(elapsed.from_git(str(repo)), named=True)}
    assert sp["v1.1"]["commits"] == 2 and sp["v1.1"]["minutes"] == 45
    assert elapsed.main(["--git", str(repo), "--tags", "v9"]) == 2


# --- the series log's durations (log #45 to log #78) ----------------------------

def test_no_duration_is_recorded_in_the_series_log():
    f = catchlog.fields(catchlog.read_log(THROUGH_78, columns_only=True))
    dur = f["columns"]["Duration (minutes)"]
    assert sum(dur[p]["filled"] for p in dur) == 0
    assert sum(dur[p]["pending"] for p in dur) == 34


@pytest.mark.parametrize("value", ["記録なし（2026-10-20には判断待ちとして挙がっていた）", "not recorded (see note)", "(TBD) (later)"])
def test_marker_with_a_note_is_pending(value):
    assert catchlog.state(value) == "pending"


@pytest.mark.parametrize("value", ["記録なしの資料を引いたため、主張が崩れる", "Not recorded because the clock was off",
                                   "記録なし（原典）を引いたため、主張が崩れる（大）", "N/A (none) — but the claim fails (large)",
                                   "—（未判断）を…（大）"])
def test_marker_in_an_answer_is_still_an_answer(value):
    assert catchlog.state(value) == "filled"


# --- review of 0de5a3a (2026-10-24) --------------------------------------------

def test_bom_is_read(tmp_path):
    p = tmp_path / "bom.jsonl"
    p.write_text("\ufeff" + json.dumps(D("a")) + "\n", encoding="utf-8")
    assert debtcheck.main([str(p), "--check"]) == 0


def test_withdrawal_closes_without_payment(tmp_path):
    p = write(tmp_path, [D("a", condition="if confirmed"), E("e", on="2026-10-05"), W("w", "a", on="2026-10-04")])
    rep = debtcheck.report(debtcheck.load(p), "2026-10-06")["Paper"]
    assert (rep["open"], rep["withdrawn"], rep["overdue"]) == (0, 1, [])


def test_overdue_conditional_is_marked(tmp_path):
    p = write(tmp_path, [D("a", condition="if confirmed"), E("e", on="2026-10-05")])
    out = debtcheck.render(debtcheck.report(debtcheck.load(p), "2026-10-06"), "2026-10-06")
    assert "OVERDUE log #1" in out and "conditional: if confirmed" in out


def test_documents_appear_from_their_first_dated_line(tmp_path):
    p = write(tmp_path, [D("a", recorded_on="2026-10-08", found_on="2026-10-08"), E("x", doc="Other", on="2026-10-09")])
    assert debtcheck.report(debtcheck.load(p), "2026-10-07") == {}
    assert list(debtcheck.report(debtcheck.load(p), "2026-10-08")) == ["Paper"]


def test_named_edition_published_before_the_deferral_is_overdue(tmp_path):
    # The rule for a named edition does not look at the day the deferral was recorded.
    p = write(tmp_path, [E("e", ed="v3", on="2026-10-01"), D("a", fix_in="v3", recorded_on="2026-10-02", found_on="2026-10-02")])
    assert [o["id"] for o in debtcheck.report(debtcheck.load(p), "2026-10-03")["Paper"]["overdue"]] == ["a"]


def test_elapsed_alias_and_prerelease_tags(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    env = {**os.environ, "GIT_AUTHOR_NAME": "a", "GIT_AUTHOR_EMAIL": "a@x", "GIT_COMMITTER_NAME": "a", "GIT_COMMITTER_EMAIL": "a@x"}

    def git(*a, when=None):
        e = dict(env)
        if when:
            e["GIT_COMMITTER_DATE"] = e["GIT_AUTHOR_DATE"] = when
        subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, env=e)
    git("init", "-q")
    steps = [("2026-10-01T09:00:00+09:00", "Kit v1.1: start", ["v1.1-rc1"]),
             ("2026-10-01T10:00:00+09:00", "Kit v1.1: release", ["v1.1", "v1.1.0"]),
             ("2026-10-02T09:00:00+09:00", "Kit v1.2: work", []),
             ("2026-10-02T09:30:00+09:00", "Merge branch 'kit-v1.2'", ["v1.2"])]
    for i, (when, msg, tags) in enumerate(steps):
        (repo / "f").write_text(str(i))
        git("add", "f")
        git("commit", "-q", "-m", msg, when=when)
        for t in tags:
            git("tag", t)
    sp = {s["tag"]: s for s in elapsed.spans(elapsed.from_git(str(repo)))}
    assert sp["v1.1"]["commits"] == 1 and sp["v1.1"]["first_commit"] == sp["v1.1"]["last_commit"]
    assert sp["v1.1.0"]["note"] == "same commit as v1.1" and sp["v1.1.0"]["minutes"] is None
    assert sp["v1.2"]["commits"] == 2 and sp["v1.2"]["minutes"] == 30
    named = {s["tag"]: s for s in elapsed.spans(elapsed.from_git(str(repo)), named=True)}
    assert named["v1.2"]["commits"] == 2 and named["v1.2"]["minutes"] == 30  # ends at the tagged merge commit
    assert elapsed.spans(elapsed.from_git(str(repo), ["v1.2", "v1.2"]))[0]["tag"] == "v1.2"
    assert len(elapsed.spans(elapsed.from_git(str(repo), ["v1.2", "v1.2"]), ["v1.2", "v1.2"])) == 1


def test_elapsed_refuses_a_shallow_clone(tmp_path, capsys):
    src = tmp_path / "src"
    src.mkdir()
    subprocess.run(["git", "-C", str(src), "init", "-q"], check=True)
    env = {**os.environ, "GIT_AUTHOR_NAME": "a", "GIT_AUTHOR_EMAIL": "a@x", "GIT_COMMITTER_NAME": "a", "GIT_COMMITTER_EMAIL": "a@x"}
    for i in range(2):
        (src / "f").write_text(str(i))
        subprocess.run(["git", "-C", str(src), "add", "f"], check=True, env=env)
        subprocess.run(["git", "-C", str(src), "commit", "-q", "-m", f"c{i}"], check=True, env=env)
    subprocess.run(["git", "-C", str(src), "tag", "v1"], check=True)
    dst = tmp_path / "dst"
    subprocess.run(["git", "clone", "-q", "--depth", "1", "file://" + str(src), str(dst)], check=True, capture_output=True)
    assert elapsed.main(["--git", str(dst)]) == 2
    assert "shallow" in capsys.readouterr().err


def test_elapsed_shows_the_time_zone():
    out = elapsed.render(elapsed.spans(elapsed.from_tsv(TIMES), named=True))
    assert "2026-10-23T10:41:44+09:00 db7c95a" in out
