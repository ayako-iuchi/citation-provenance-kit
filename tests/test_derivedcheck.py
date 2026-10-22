"""Tests for tools/derivedcheck.py (kit v1.10).

Run: python3 -m pytest tests
"""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import derivedcheck as dc  # noqa: E402
import statuslog  # noqa: E402

DERIVED = os.path.join(ROOT, "register", "derived.jsonl")
STATUS = os.path.join(ROOT, "register", "status_log.jsonl")
TOOL = os.path.join(ROOT, "tools", "derivedcheck.py")
SUMMARY = "What the buyer is defending (one-page summary)"


def run(*args):
    return subprocess.run([sys.executable, TOOL, *args], capture_output=True, text=True)


def by(results, derived, made_from):
    hits = [r for r in results if r["derived"] == derived and r["made_from"] == made_from]
    assert len(hits) == 1, hits
    return hits[0]


# --- the register ----------------------------------------------------------------

def test_register_reads_and_has_no_problems():
    records = dc.load(DERIVED)
    assert dc.check_log(records) == []
    assert {r["id"] for r in records} >= {"2026-10-22-01", "2026-10-22-02"}


def test_register_matches_schema():
    jsonschema = pytest.importorskip("jsonschema")
    with open(os.path.join(ROOT, "schema", "derived.schema.json"), encoding="utf-8") as f:
        schema = json.load(f)
    for r in dc.load(DERIVED):
        jsonschema.validate(r, schema)


def test_summary_v1_0_is_stale_and_v1_1_current():
    """v1.0 named the edition it was made from; the source moved two days later."""
    res = dc.verdicts(dc.load(DERIVED), statuslog.load(STATUS), "2026-10-22")
    old = by(res, f"{SUMMARY} v1.0", "v1.0")
    new = by(res, f"{SUMMARY} v1.1", "v1.1")
    assert old["verdict"] == "stale" and old["source_now"] == "1.1"
    assert "not-in-document" not in old["flags"]  # it did say what it was made from
    assert new["verdict"] == "current"


def test_the_record_that_ran_ahead_of_the_fact_is_flagged():
    """The method paper (12 October) said v1.1 was issued; it was issued on 13 October."""
    res = dc.verdicts(dc.load(DERIVED), statuslog.load(STATUS), "2026-10-22")
    new = by(res, f"{SUMMARY} v1.1", "v1.1")
    assert new["flags"] == ["claimed-before-observed"]


def test_kit_made_from_two_editions_gets_two_verdicts():
    res = dc.verdicts(dc.load(DERIVED), statuslog.load(STATUS), "2026-10-22")
    kit = [r for r in res if r["derived"].startswith("Citation provenance kit")]
    assert sorted((r["made_from"], r["verdict"]) for r in kit) == [("v1.1", "stale"), ("v1.2", "current")]


def test_a_source_with_no_version_is_unknown_not_current():
    res = dc.verdicts(dc.load(DERIVED), statuslog.load(STATUS), "2026-10-22")
    paste = [r for r in res if "paste kit" in r["derived"]]
    assert paste and all(r["verdict"] == "source-unknown" for r in paste)
    assert all("not-in-document" in r["flags"] for r in paste)


def test_reading_the_register_as_it_stood_earlier():
    """Nothing in this register was recorded before 22 October."""
    assert dc.verdicts(dc.load(DERIVED), statuslog.load(STATUS), "2026-10-21") == []


# --- verdicts on made-up records ---------------------------------------------------

def rec(**kw):
    r = {"id": "x1", "derived": {"title": "Deck", "version": "v1"},
         "from": [{"title": "Paper", "version": "v2", "as_stated": "from Paper v2"}],
         "recorded_on": "2026-01-01", "recorded_by": "test"}
    r.update(kw)
    return r


def status_line(value, expires=None, recorded="2026-01-01"):
    return {"id": "s1", "subject": "Paper", "component": "edition", "value": value,
            "grade": "A", "recorded_on": recorded, "source": "test", "expires_on": expires}


def test_claimed_with_no_observation_is_both_flags():
    r = rec(claimed={"on": "2026-01-02", "by": "a log"}, observed=None)
    v = dc.verdicts([r], [status_line("v2")], "2026-02-01")[0]
    assert v["flags"] == ["claimed-before-observed", "unobserved"]


def test_claimed_after_it_was_seen_is_not_flagged():
    r = rec(claimed={"on": "2026-01-05", "by": "a log"}, observed={"on": "2026-01-03", "how": "opened it"})
    assert dc.verdicts([r], [status_line("v2")], "2026-02-01")[0]["flags"] == []


def test_issued_and_never_seen_is_unobserved():
    r = rec(issued_on="2026-01-02")
    assert dc.verdicts([r], [status_line("v2")], "2026-02-01")[0]["flags"] == ["unobserved"]


def test_expired_source_edition_is_not_compared():
    v = dc.verdicts([rec()], [status_line("v2", expires="2026-01-10")], "2026-02-01")[0]
    assert v["verdict"] == "source-expired" and v["source_now"] is None


def test_a_superseded_record_is_not_checked():
    a = rec(id="a", **{"from": [{"title": "Paper", "version": "v1", "as_stated": "x"}]})
    b = rec(id="b", supersedes="a")
    res = dc.verdicts([a, b], [status_line("v2")], "2026-02-01")
    assert [r["record"] for r in res] == ["b"] and res[0]["verdict"] == "current"


def test_supersedes_must_point_back():
    a = rec(id="a", supersedes="b")
    b = rec(id="b")
    assert dc.check_log([a, b]) == ["line 1: supersedes b, which is not recorded earlier"]


def test_version_of():
    assert dc.version_of("v1.1 (26 July 2026)") == "1.1"
    assert dc.version_of("Kit v1.10") == "1.10"
    assert dc.version_of("1.1.1") == "1.1.1"
    assert dc.version_of("26 July 2026") is None
    assert dc.version_of(None) is None


@pytest.mark.parametrize("line,msg", [
    ("{", "not JSON"),
    ('[1]', "JSON object"),
    ('{"id": "a"}', "missing"),
    ('{"id": "a", "derived": {"title": "D", "version": "1"}, "from": [], "recorded_on": "2026-01-01", "recorded_by": "t"}', "at least one"),
    ('{"id": "a", "derived": {"title": "D", "version": "1"}, "from": [{"title": "P", "version": "1"}], "recorded_on": "yesterday", "recorded_by": "t"}', "not a date"),
    ('{"id": "a", "derived": {"title": "D", "version": "1"}, "from": [{"title": "P", "version": "1"}], "recorded_on": "2026-01-01", "recorded_by": "t", "observed": {"how": "x"}}', "observed"),
    ('{"id": "a", "derived": {"title": "D", "version": "1"}, "from": [{"title": "P", "version": "1"}], "recorded_on": "2026-01-01", "recorded_by": "t", "seen": true}', "unknown key"),
])
def test_malformed_records_exit_2(tmp_path, line, msg):
    p = tmp_path / "d.jsonl"
    p.write_text(line + "\n", encoding="utf-8")
    with pytest.raises(dc.Malformed, match=msg):
        dc.load(str(p))
    r = run("--log", str(p), "--status", STATUS)
    assert r.returncode == 2 and msg.split()[0] in r.stderr


def test_command_line_exit_status():
    r = run("--log", DERIVED, "--status", STATUS, "--on", "2026-10-22")
    assert r.returncode == 1  # stale and flagged entries are reported
    assert "claimed-before-observed" in r.stdout
    r = run("--log", DERIVED, "--status", STATUS, "--on", "2026-10-21")
    assert r.returncode == 0


# --- the version labels of a tree ------------------------------------------------

def make_tree(tmp_path, cff="1.3", readme="1.3", build="1.1", changelog="1.3", tags=None):
    (tmp_path / "tools").mkdir()
    (tmp_path / "CITATION.cff").write_text(
        f'cff-version: 1.2.0\nversion: "{cff}"\nreferences:\n  - type: report\n    version: "1.1"\n', encoding="utf-8")
    tag_line = ""
    if tags is not None:
        tag_line = "\nEach release is tagged (" + ", ".join(f"`{t}`" for t in tags) + ").\n"
    (tmp_path / "README.md").write_text(
        f"# Kit\n\nReproduction kit for **What Breaks in a Citation** (v1.1, 26 July 2026) by A.\nKit v{readme} · CC0\n{tag_line}",
        encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(f"# Changelog\n\n## Kit v{changelog} — 2026-10-20\n\n## Kit v1.2\n", encoding="utf-8")
    (tmp_path / "tools" / "build_kit.py").write_text(
        f'KIT_VERSION = "{build}"\nPAPER = "What Breaks in a Citation, v1.1 (26 July 2026)"\n', encoding="utf-8")
    return str(tmp_path)


def test_tree_labels_found_and_disagreement_reported(tmp_path):
    root = make_tree(tmp_path)
    kit, paper = dc.tree_labels(root)
    assert dict(kit) == {"CITATION.cff version": "1.3", "README.md header": "1.3",
                         "CHANGELOG.md latest entry": "1.3", "tools/build_kit.py KIT_VERSION": "1.1"}
    assert {v for _, v in paper} == {"1.1"}
    # Without --expect nothing is assumed right: every place is listed.
    assert len(dc.tree_problems(kit)) == 4
    assert dc.tree_problems(kit, "v1.3") == [("tools/build_kit.py KIT_VERSION", "1.1", "1.3")]


def test_tree_that_agrees_reports_nothing(tmp_path):
    root = make_tree(tmp_path, build="1.3")
    kit, _ = dc.tree_labels(root)
    assert dc.tree_problems(kit) == []
    assert run("--tree", root).returncode == 0
    assert run("--tree", root, "--expect", "1.4").returncode == 1


def test_claimed_tags_against_existing_ones(tmp_path):
    root = make_tree(tmp_path, build="1.3", tags=["v1.0", "v1.1.1", "v1.3"])
    assert dc.claimed_tags(root) == ["v1.0", "v1.1.1", "v1.3"]
    r = run("--tree", root, "--tags", "v1.0,v1.1.1")
    assert r.returncode == 1 and "CLAIMED, NOT FOUND: tag v1.3" in r.stdout
    assert run("--tree", root, "--tags", "v1.0,v1.1.1,v1.3").returncode == 0


def test_the_kit_tree_itself_agrees():
    """This release names one version everywhere, including the workbook."""
    kit, paper = dc.tree_labels(ROOT)
    places = dict(kit)
    assert "workbook Start here A2" in places
    assert dc.tree_problems(kit) == [], kit
    # Made for v1.1; files made from v1.2 name it (the author's decision, 22 October 2026).
    assert {v for _, v in paper} == {"1.1", "1.2"}


def _has_ref(ref):
    r = subprocess.run(["git", "-C", ROOT, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}"],
                       capture_output=True)
    return r.returncode == 0


@pytest.mark.parametrize("tag,places", [
    ("v1.2", {"CITATION.cff version", "tools/build_kit.py KIT_VERSION", "workbook Start here A2"}),  # #47, #65
    ("v1.7", {"tools/build_kit.py KIT_VERSION", "workbook Start here A2"}),                         # #65
    ("v1.8", set()),
    ("9883c3f", {"tools/build_kit.py KIT_VERSION", "workbook Start here A2"}),                      # #74
])
def test_past_releases(tag, places):
    """Run on the published tags: the two recorded failures are found where they were."""
    if not _has_ref(tag):
        pytest.skip(f"tag {tag} not in this clone")
    kit, _ = dc.tree_labels(ROOT, tag)
    expect = "v1.9" if tag == "9883c3f" else tag
    assert {p for p, _, _ in dc.tree_problems(kit, expect)} == places


# --- added after the review of 22 October 2026 -------------------------------------

@pytest.mark.parametrize("text,want", [
    ("v1.1 (26 July 2026)", "1.1"), ("Kit v1.10", "1.10"), ("V1.0 EN", "1.0"), ("v2", "2"),
    ("1.1.1", "1.1.1"), ("Section 2.1 says v1.1", "1.1"), ("10.1234/abc v1.2", "1.2"),
    ("論文のv1.2", "1.2"), ("キットv1.4からの例外", "1.4"),
    ("2026.10.12", None), ("20.10.2026", None), ("2026-10-22", None), ("12", None), ("v2026", None),
])
def test_version_of_reads_versions_not_dates(text, want):
    assert dc.version_of(text) == want


def test_v1_and_1_0_are_the_same_version():
    v = dc.verdicts([rec(**{"from": [{"title": "Paper", "version": "v1", "as_stated": "x"}]})],
                    [status_line("1.0")], "2026-02-01")[0]
    assert v["verdict"] == "current"


def test_an_unknown_edition_is_not_stale():
    v = dc.verdicts([rec(**{"from": [{"title": "Paper", "version": None, "as_stated": None}]})],
                    [status_line("v2")], "2026-02-01")[0]
    assert v["verdict"] == "made-from-unknown"
    v = dc.verdicts([rec()], [status_line("July 2026 edition")], "2026-02-01")[0]
    assert v["verdict"] == "source-unknown"


def test_claimed_on_the_day_it_was_seen_is_not_flagged():
    r = rec(claimed={"on": "2026-01-03", "by": "a log"}, observed={"on": "2026-01-03", "how": "opened it"})
    assert dc.verdicts([r], [status_line("v2")], "2026-02-01")[0]["flags"] == []
    r = rec(claimed={"on": "2026-01-03", "by": "a log"}, observed={"on": "2026-01-04", "how": "opened it"})
    assert dc.verdicts([r], [status_line("v2")], "2026-02-01")[0]["flags"] == ["claimed-before-observed"]


def test_a_supersedes_recorded_after_on_does_not_count():
    a = rec(id="a", **{"from": [{"title": "Paper", "version": "v1", "as_stated": "x"}]})
    b = rec(id="b", supersedes="a", recorded_on="2026-03-01")
    res = dc.verdicts([a, b], [status_line("v2")], "2026-02-01")
    assert [(r["record"], r["verdict"]) for r in res] == [("a", "stale")]


def test_supersedes_about_another_document_is_a_problem():
    a = rec(id="a")
    b = rec(id="b", supersedes="a", derived={"title": "Poster", "version": "v1"})
    assert dc.check_log([a, b]) == ["line 2: supersedes a, which is about another document ('Deck')"]


def test_an_older_version_of_the_same_copy_is_flagged_replaced():
    old = rec(id="a", derived={"title": "Deck", "version": "v1"},
              **{"from": [{"title": "Paper", "version": "v1", "as_stated": "x"}]})
    new = rec(id="b", derived={"title": "Deck", "version": "v2"})
    res = {r["record"]: r for r in dc.verdicts([old, new], [status_line("v2")], "2026-02-01")}
    assert res["a"]["verdict"] == "stale" and "replaced-by-v2" in res["a"]["flags"]
    assert res["b"]["flags"] == []


@pytest.mark.parametrize("line,msg", [
    ('{"id": "a", "supersedes": ["x"], "derived": {"title": "D", "version": "1"}, "from": [{"title": "P", "version": "1"}], "recorded_on": "2026-01-01", "recorded_by": "t"}', "supersedes"),
    ('{"id": 3, "derived": {"title": "D", "version": "1"}, "from": [{"title": "P", "version": "1"}], "recorded_on": "2026-01-01", "recorded_by": "t"}', "id"),
    ('{"id": "a", "copies": "x", "derived": {"title": "D", "version": "1"}, "from": [{"title": "P", "version": "1"}], "recorded_on": "2026-01-01", "recorded_by": "t"}', "copies"),
])
def test_wrong_types_are_malformed(tmp_path, line, msg):
    p = tmp_path / "d.jsonl"
    p.write_text(line + "\n", encoding="utf-8")
    with pytest.raises(dc.Malformed, match=msg):
        dc.load(str(p))


def test_bad_input_exits_2_without_a_traceback(tmp_path):
    bad = tmp_path / "d.jsonl"
    bad.write_bytes(b"\xff\xfe not utf-8\n")
    r = run("--log", str(bad), "--status", STATUS)
    assert r.returncode == 2 and "Traceback" not in r.stderr
    status = tmp_path / "s.jsonl"
    status.write_text(json.dumps(status_line("v2", recorded="yesterday")) + "\n", encoding="utf-8")
    good = tmp_path / "g.jsonl"
    good.write_text(json.dumps(rec()) + "\n", encoding="utf-8")
    r = run("--log", str(good), "--status", str(status), "--on", "2026-02-01")
    assert r.returncode == 2 and "Traceback" not in r.stderr


def test_missing_tree_and_ref_exit_2(tmp_path):
    assert run("--tree", str(tmp_path / "nowhere")).returncode == 2
    assert run("--tree", str(tmp_path)).returncode == 2           # no labels: not a kit
    assert run("--tree", ROOT, "--ref", "no-such-ref-xyz").returncode == 2
    assert run("--log", DERIVED, "--status", STATUS, "--ref", "v1.0").returncode == 2


def test_tags_read_from_ls_remote_output(tmp_path):
    (tmp_path / "t").mkdir()
    root = make_tree(tmp_path / "t", build="1.3", tags=["v1.0", "v1.3"])
    f = tmp_path / "tags.txt"
    f.write_text("abc\trefs/tags/v1.0\nabd\trefs/tags/v1.0^{}\nabe\trefs/tags/v1.3\n", encoding="utf-8")
    r = run("--tree", root, "--tags", "@" + str(f))
    assert r.returncode == 0, r.stdout


def test_the_readme_tag_list_is_read():
    tags = dc.claimed_tags(ROOT)
    assert tags[:2] == ["v1.0", "v1.1"] and "v1.9" in tags


def test_every_edition_a_label_names_is_listed():
    _, paper = dc.tree_labels(ROOT)
    for place in ("README.md header", "README_ja.md header", "tools/build_kit.py PAPER", "workbook Start here A2"):
        assert sorted(v for p, v in paper if p == place) == ["1.1", "1.2"], place


def test_the_kit_label_is_read_from_the_start_of_a_line(tmp_path):
    root = make_tree(tmp_path, build="1.3")
    readme = tmp_path / "README.md"
    readme.write_text("# Kit\n\nSee the exceptions (from Kit v1.1).\n", encoding="utf-8")
    kit, _ = dc.tree_labels(root)
    assert dict(kit)["README.md header"] is None


def _xlsx(path, sheet_target, cell_xml, shared=None):
    import zipfile
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/workbook.xml",
                   '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                   '<sheets><sheet name="Other" sheetId="1" r:id="rId1"/><sheet name="Start here" sheetId="2" r:id="rId2"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/>'
                   f'<Relationship Id="rId2" Target="{sheet_target}"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml",
                   '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
                   '<row r="1"><c r="A1" t="inlineStr"><is><t>Kit v9.9</t></is></c></row></sheetData></worksheet>')
        z.writestr(sheet_target.lstrip("/") if sheet_target.startswith("/xl/") else "xl/" + sheet_target,
                   '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
                   f'<row r="2">{cell_xml}</row></sheetData></worksheet>')
        if shared is not None:
            z.writestr("xl/sharedStrings.xml",
                       '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' + shared + "</sst>")


def test_workbook_inline_strings_and_an_absolute_sheet_path(tmp_path):
    p = tmp_path / "w.xlsx"
    _xlsx(p, "/xl/worksheets/start.xml",
          '<c r="A2" t="inlineStr"><is><t>Kit v1.3 · accompanies What Breaks in a Citation, v1.1 (26 July 2026)</t></is></c>')
    assert dc._xlsx_strings(p.read_bytes()) == [("A2", "Kit v1.3 · accompanies What Breaks in a Citation, v1.1 (26 July 2026)")]


def test_workbook_shared_strings_skip_phonetic_runs(tmp_path):
    p = tmp_path / "w.xlsx"
    _xlsx(p, "worksheets/sheet2.xml", '<c r="A2" t="s"><v>0</v></c>',
          shared='<si><r><t>Kit v1.3</t></r><rPh sb="0" eb="1"><t>キット</t></rPh></si>')
    assert dc._xlsx_strings(p.read_bytes()) == [("A2", "Kit v1.3")]


def test_an_unknown_ref_says_so():
    r = run("--tree", ROOT, "--ref", "no-such-ref-xyz")
    assert r.returncode == 2 and "not a commit" in r.stderr


def test_only_the_readme_header_is_read_for_the_kit_label(tmp_path):
    root = make_tree(tmp_path, build="1.3")
    readme = tmp_path / "README.md"
    readme.write_text("# Kit\n\nReproduction kit.\n\n\n\n\n\n\nKit v9.9 is mentioned here, below the header.\n", encoding="utf-8")
    kit, _ = dc.tree_labels(root)
    assert dict(kit)["README.md header"] is None


def test_a_bad_status_date_names_the_line(tmp_path):
    status = tmp_path / "s.jsonl"
    status.write_text(json.dumps(status_line("v2", recorded="yesterday")) + "\n", encoding="utf-8")
    good = tmp_path / "g.jsonl"
    good.write_text(json.dumps(rec()) + "\n", encoding="utf-8")
    r = run("--log", str(good), "--status", str(status), "--on", "2026-02-01")
    assert r.returncode == 2 and "line 1: recorded_on" in r.stderr


def test_the_register_was_only_appended_to():
    """The first four records stand as first written (kit v1.10's draft, 1256ee8)."""
    r = subprocess.run(["git", "-C", ROOT, "show", "1256ee8:register/derived.jsonl"], capture_output=True, text=True)
    if r.returncode != 0:
        pytest.skip("commit 1256ee8 not in this clone")
    with open(DERIVED, encoding="utf-8") as f:
        now = [l.rstrip("\n") for l in f if l.strip()]
    first = [l for l in r.stdout.splitlines() if l.strip()]
    assert now[: len(first)] == first
