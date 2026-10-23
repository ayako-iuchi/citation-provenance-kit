"""Tests for tools/idcheck.py (kit v1.12).

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

import idcheck as ic  # noqa: E402

NAMESPACES = os.path.join(ROOT, "register", "namespaces.json")
IDENTIFIERS = os.path.join(ROOT, "register", "identifiers.jsonl")
TOOL = os.path.join(ROOT, "tools", "idcheck.py")
SHA_2021 = "7baa01f3f3c64ff3bb0ecdf85e914427f829ba9f940d4aee59657f623d54d7d9"


def run(*args):
    return subprocess.run([sys.executable, TOOL, *args], capture_output=True, text=True)


@pytest.fixture(scope="module")
def ns():
    return ic.load_namespaces(NAMESPACES)


@pytest.fixture(scope="module")
def reg(ns):
    return ic.load(IDENTIFIERS, ns)


def rec(**over):
    r = {"id": "t-1", "namespace": "gsr", "number": "206(E)",
         "key": {"date": "2021-03-24", "amends": "Companies (Audit and Auditors) Rules 2014"},
         "what": "test", "source": "test", "recorded_on": "2026-10-23", "recorded_by": "test"}
    r.update(over)
    return r


def write(tmp_path, records, name="ids.jsonl"):
    p = tmp_path / name
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    return str(p)


# --- the register ---------------------------------------------------------------

def test_register_loads(reg):
    assert len(reg) >= 16
    assert {r["namespace"] for r in reg} == {"gsr", "om", "blog", "log", "file"}


def test_register_first_lines_stand_as_written():
    # Records are appended, never edited: the first sixteen keep their ids and numbers.
    with open(IDENTIFIERS, encoding="utf-8") as f:
        first = [json.loads(l) for l in f if l.strip()][:16]
    assert [(r["id"], r["namespace"], r["number"]) for r in first] == [
        ("2026-10-23-01", "gsr", "205(E)"), ("2026-10-23-02", "gsr", "206(E)"),
        ("2026-10-23-03", "gsr", "206(E)"), ("2026-10-23-04", "om", "F.1/1/2021-PPD"),
        ("2026-10-23-05", "om", "F./1/9/2021-PPD"), ("2026-10-23-06", "blog", "18"),
        ("2026-10-23-07", "blog", "19"), ("2026-10-23-08", "blog", "22"),
        ("2026-10-23-09", "blog", "30"), ("2026-10-23-10", "blog", "31"),
        ("2026-10-23-11", "log", "22"), ("2026-10-23-12", "log", "30"),
        ("2026-10-23-13", "log", "32"), ("2026-10-23-14", "log", "48"),
        ("2026-10-23-15", "file", "echap06_vol1.pdf"), ("2026-10-23-16", "file", "echap06_vol1.pdf")]


def test_2021_hash_matches_the_es2021_example():
    with open(os.path.join(ROOT, "examples", "es2021_ch6", "lines.json"), encoding="utf-8") as f:
        lines = json.load(f)
    assert lines["source"]["file_sha256"] == SHA_2021
    r = [r for r in ic.current(ic.load(IDENTIFIERS, ic.load_namespaces(NAMESPACES)))
         if r["key"].get("sha256") == SHA_2021]
    assert len(r) == 1 and r[0]["key"]["url"] == lines["source"]["url"]


def test_check_on_the_register(reg, ns):
    flags = {(f["flag"], f.get("namespace") or "/".join(f.get("namespaces", []))) for f in ic.check(reg, ns)}
    assert ("number-shared", "gsr") in flags
    assert ("date-shared", "gsr") in flags
    assert ("date-shared", "om") in flags
    assert ("name-shared", "file") in flags
    assert ("bare-overlap", "blog/log") in flags
    # A file's number is its name; name-shared says it, not number-shared too.
    assert ("number-shared", "file") not in flags


def test_number_shared_lists_the_fields_that_separate(reg, ns):
    f = [f for f in ic.check(reg, ns) if f["flag"] == "number-shared" and f["namespace"] == "gsr"][0]
    assert f["fields"] == ["date", "amends"]


def test_bare_overlap_spans(reg, ns):
    f = [f for f in ic.check(reg, ns) if f["flag"] == "bare-overlap"][0]
    assert f["numbers"] == [[1, 36]]


def test_dash_is_key_incomplete(tmp_path, ns):
    path = write(tmp_path, [rec(key={"date": "2021-03-24", "amends": "—"})])
    f = ic.check(ic.load(path, ns), ns)
    assert f[0]["flag"] == "key-incomplete" and f[0]["fields"] == ["amends"]


def test_missing_key_field_is_key_incomplete(tmp_path, ns):
    path = write(tmp_path, [rec(key={"date": "2021-03-24"})])
    assert ic.check(ic.load(path, ns), ns)[0]["fields"] == ["amends"]


def test_superseded_record_is_not_checked(tmp_path, ns):
    old = rec(id="a", key={"date": "2021-03-24", "amends": "—"})
    new = rec(id="b", supersedes="a")
    found = [f for f in ic.check(ic.load(write(tmp_path, [old, new]), ns), ns) if f["flag"] != "bare-overlap"]
    assert found == []


def test_same_name_with_unhashed_file_is_name_shared(tmp_path, ns):
    a = rec(id="a", namespace="file", number="x.pdf",
            key={"name": "x.pdf", "url": "u1", "sha256": "a" * 64, "edition": "1"})
    b = rec(id="b", namespace="file", number="x.pdf",
            key={"name": "x.pdf", "url": "u2", "sha256": "—", "edition": "2"})
    flags = [f["flag"] for f in ic.check(ic.load(write(tmp_path, [a, b]), ns), ns)]
    assert "name-shared" in flags


# --- resolving --------------------------------------------------------------------

def test_number_alone_is_ambiguous(reg, ns):
    r = ic.resolve(reg, ns, "gsr", "206(E)")
    assert r["verdict"] == "ambiguous" and r["separate_by"] == ["date", "amends"]


def test_date_alone_does_not_separate_205_and_206(reg, ns):
    # Number + date separates 206(E) of 2015 from 206(E) of 2021 …
    assert ic.resolve(reg, ns, "gsr", "206(E)", {"date": "2021-03-24"})["verdict"] == "unique"
    # … and the date is shared with 205(E): the number is still needed.
    hits = [r for r in reg if r["namespace"] == "gsr" and r["key"].get("date") == "2021-03-24"]
    assert len(hits) == 2


def test_wrong_title_is_mismatch_and_names_the_number_that_fits(reg, ns):
    # Entry #48: "Blog #18" written where #19 was meant.
    r = ic.resolve(reg, ns, "blog", "18", {"title": "A Rule Is Not a Mechanism"})
    assert r["verdict"] == "mismatch"
    assert [m["number"] for m in r["key_matches"]] == ["19"]


def test_absent(reg, ns):
    assert ic.resolve(reg, ns, "gsr", "999(E)")["verdict"] == "absent"


def test_resolve_matches_ignore_case_and_width(reg, ns):
    assert ic.resolve(reg, ns, "gsr", "２０６(e)", {"date": "2015-03-18"})["verdict"] == "unique"


def test_resolve_unknown_key_field_is_malformed(reg, ns):
    with pytest.raises(ic.Malformed):
        ic.resolve(reg, ns, "gsr", "206(E)", {"title": "x"})


def test_cli_resolve_exit_codes():
    assert run("--resolve", "gsr", "206(E)", "--key", "date=2015-03-18").returncode == 0
    assert run("--resolve", "gsr", "206(E)").returncode == 1
    assert run("--resolve", "nope", "1").returncode == 2
    assert run("--resolve", "gsr", "206(E)", "--key", "date").returncode == 2


# --- files ------------------------------------------------------------------------

def test_two_files_one_name(tmp_path, ns):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "echap06_vol1.pdf").write_bytes(b"one edition")
    (b / "echap06_vol1.pdf").write_bytes(b"another edition")
    records = [
        rec(id="x", namespace="file", number="echap06_vol1.pdf",
            key={"name": "echap06_vol1.pdf", "url": "u1",
                 "sha256": hashlib.sha256(b"one edition").hexdigest(), "edition": "2020-21"}),
        rec(id="y", namespace="file", number="echap06_vol1.pdf",
            key={"name": "echap06_vol1.pdf", "url": "u2",
                 "sha256": hashlib.sha256(b"another edition").hexdigest(), "edition": "2018-19"}),
    ]
    reg = ic.load(write(tmp_path, records), ns)
    ra = ic.find_file(reg, str(a / "echap06_vol1.pdf"))
    rb = ic.find_file(reg, str(b / "echap06_vol1.pdf"))
    assert ra["by_name"] == rb["by_name"] == ["x", "y"]
    assert ra["by_content"] == ["x"] and rb["by_content"] == ["y"]
    assert ra["verdict"] == rb["verdict"] == "unique"


def test_unregistered_file_is_absent(tmp_path, reg):
    p = tmp_path / "echap06_vol1.pdf"
    p.write_bytes(b"not the chapter")
    r = ic.find_file(reg, str(p))
    assert r["verdict"] == "absent" and len(r["by_name"]) == 2


def test_cli_file_exit_codes(tmp_path):
    p = tmp_path / "echap06_vol1.pdf"
    p.write_bytes(b"x")
    assert run("--file", str(p)).returncode == 1
    assert run("--file", str(tmp_path / "missing.pdf")).returncode == 2


# --- scanning ---------------------------------------------------------------------

def verdicts(text, ns):
    return [(t["token"], t["verdict"], t.get("namespace")) for t in ic.scan_text(text, ns)]


def test_named_tokens(ns):
    v = verdicts("Hypothetical Technical Blog #30 and log #30 and entry #34; Blog #31", ns)
    assert v == [("#30", "named", "blog"), ("#30", "named", "log"),
                 ("#34", "named", "log"), ("#31", "named", "blog")]


def test_bare_token_in_both_namespaces_is_ambiguous(ns):
    t = ic.scan_text("the shape of #30, the other way round", ns)[0]
    assert t["verdict"] == "ambiguous" and t["candidates"] == ["blog", "log"]


def test_planned_number_counts(ns):
    # #32 is a log entry and a planned post.
    t = ic.scan_text("see #32", ns)[0]
    assert t["verdict"] == "ambiguous" and t["candidates"] == ["log"] and t["planned"] == ["blog"]


def test_number_in_one_namespace_only_is_unqualified(ns):
    t = ic.scan_text("entry, as #76 says", ns)[0]
    assert t["verdict"] == "unqualified" and t["candidates"] == ["log"]


def test_number_in_none_is_unknown(ns):
    assert ic.scan_text("#900", ns)[0]["verdict"] == "unknown"


def test_range_and_list_inherit_the_name(ns):
    v = verdicts("entries #26–#42, Blog #1–#16, log #43 and #44, ログ#45〜#48", ns)
    assert [x[1] for x in v] == ["named"] * 8
    assert [x[2] for x in v] == ["log", "log", "blog", "blog", "log", "log", "log", "log"]


def test_inheritance_needs_a_join(ns):
    v = verdicts("log #43 was found before #44", ns)
    # #44 is past the last post, so bare it can only be the log's.
    assert v[1][1] == "unqualified"


def test_bare_range_does_not_inherit(ns):
    v = verdicts("#17〜#21", ns)
    assert [x[1] for x in v] == ["ambiguous", "ambiguous"]


def test_japanese(ns):
    v = verdicts("ログ#30は、#21の監査と、架空の技術ブログ #22の", ns)
    assert v == [("#30", "named", "log"), ("#21", "ambiguous", None), ("#22", "named", "blog")]


def test_japanese_blog_no(ns):
    assert verdicts("Hypothetical Technical Blogの#1〜#16は", ns)[0][1] == "named"


def test_full_width_hash(ns):
    assert ic.scan_text("＃30", ns)[0]["number"] == 30


def test_not_tokens(ns):
    assert ic.scan_text("#TechBlog #LLM #1st ¶6.22 C#", ns) == []


def test_word_boundary_for_latin_names(ns):
    # "catalog #30" does not name the log.
    assert verdicts("catalog #30", ns)[0][1] == "ambiguous"


def test_cli_scan(tmp_path):
    p = tmp_path / "post.txt"
    p.write_text("Blog #30 and log #30\n", encoding="utf-8")
    assert run("--scan", str(p)).returncode == 0
    p.write_text("the shape of #30\n", encoding="utf-8")
    r = run("--scan", str(p))
    assert r.returncode == 1 and "ambiguous" in r.stdout
    data = json.loads(run("--scan", str(p), "--json").stdout)
    assert data[0]["summary"]["ambiguous"] == 1


def test_cli_check():
    r = run("--check")
    assert r.returncode == 1 and "bare-overlap" in r.stdout and "name-shared" in r.stdout


# --- malformed input --------------------------------------------------------------

@pytest.mark.parametrize("over", [
    {"namespace": "nope"},
    {"key": {"date": "2021-03-24", "title": "x"}},
    {"key": {"date": "24 March 2021", "amends": "x"}},
    {"key": {"date": "2021-02-30", "amends": "x"}},
    {"key": ["date"]},
    {"number": 206},
    {"number": " "},
    {"recorded_on": "2026-13-01"},
    {"extra": 1},
    {"supersedes": "nothing"},
    {"key": {"date": "2021-03-24", "amends": 5}},
])
def test_malformed_records(tmp_path, ns, over):
    with pytest.raises(ic.Malformed):
        ic.load(write(tmp_path, [rec(**over)]), ns)


def test_bad_sha(tmp_path, ns):
    r = rec(namespace="file", number="x", key={"name": "x", "url": "u", "sha256": "ABC", "edition": "1"})
    with pytest.raises(ic.Malformed):
        ic.load(write(tmp_path, [r]), ns)


def test_duplicate_id_and_double_supersede(tmp_path, ns):
    with pytest.raises(ic.Malformed):
        ic.load(write(tmp_path, [rec(), rec()]), ns)
    with pytest.raises(ic.Malformed):
        ic.load(write(tmp_path, [rec(id="a"), rec(id="b", supersedes="a"), rec(id="c", supersedes="a")]), ns)


def test_not_json(tmp_path, ns):
    p = tmp_path / "x.jsonl"
    p.write_text("{not json\n", encoding="utf-8")
    with pytest.raises(ic.Malformed):
        ic.load(str(p), ns)
    assert run("--check", "--log", str(p)).returncode == 2


def test_namespaces_malformed(tmp_path):
    bad = [
        {"namespaces": [{"name": "a", "what": "x", "key": ["number"], "bare": True}]},
        {"namespaces": [{"name": "a", "what": "x", "key": ["t"], "bare": "yes"}]},
        {"namespaces": [{"name": "a", "what": "x", "key": ["t"], "bare": True, "exists": [[5, 1]]}]},
        {"namespaces": [{"name": "a", "what": "x", "key": ["t"], "bare": True, "names": ["log #"]},
                        {"name": "b", "what": "x", "key": ["t"], "bare": True, "names": ["Log #"]}]},
        {"namespaces": [{"name": "a", "what": "x", "key": ["t"], "bare": True},
                        {"name": "a", "what": "x", "key": ["t"], "bare": True}]},
        {"nope": []},
    ]
    for i, b in enumerate(bad):
        p = tmp_path / f"ns{i}.json"
        p.write_text(json.dumps(b), encoding="utf-8")
        with pytest.raises(ic.Malformed):
            ic.load_namespaces(str(p))


def test_key_without_resolve_is_refused():
    assert run("--check", "--key", "date=2021-03-24").returncode == 2


def test_unreadable_scan_file(tmp_path):
    p = tmp_path / "x.txt"
    p.write_bytes(b"\xff\xfe\x00bad")
    assert run("--scan", str(p)).returncode == 2


# --- the schemas and the stored output --------------------------------------------

def test_register_matches_schema(ns):
    jsonschema = pytest.importorskip("jsonschema")
    with open(os.path.join(ROOT, "schema", "identifier.schema.json"), encoding="utf-8") as f:
        schema = json.load(f)
    for r in ic.load(IDENTIFIERS, ns):
        jsonschema.validate(r, schema)


def test_namespaces_match_schema():
    jsonschema = pytest.importorskip("jsonschema")
    with open(os.path.join(ROOT, "schema", "namespaces.schema.json"), encoding="utf-8") as f:
        schema = json.load(f)
    with open(NAMESPACES, encoding="utf-8") as f:
        jsonschema.validate(json.load(f), schema)


EVIDENCE_COMMANDS = [
    ["--check"],
    ["--resolve", "gsr", "206(E)"],
    ["--resolve", "gsr", "206(E)", "--key", "date=2021-03-24"],
    ["--resolve", "gsr", "206(E)", "--key", "date=2015-03-18"],
    ["--resolve", "blog", "18", "--key", "title=A Rule Is Not a Mechanism"],
    ["--resolve", "om", "F./1/9/2021-PPD"],
    ["--scan", "README.md", "README_ja.md"],
]


def evidence_text():
    out = []
    for args in EVIDENCE_COMMANDS:
        shown = " ".join(a if " " not in a else f'"{a}"' for a in args)
        r = subprocess.run([sys.executable, TOOL, *args], capture_output=True, text=True, cwd=ROOT)
        out.append(f"$ python3 tools/idcheck.py {shown}\n{r.stdout.rstrip()}\n(exit {r.returncode})")
    return "\n\n".join(out) + "\n"


def test_evidence_reproduces():
    with open(os.path.join(ROOT, "evidence", "idcheck_2026-10-23.txt"), encoding="utf-8") as f:
        stored = f.read()
    assert stored.split("\n\n# ", 1)[0].rstrip("\n") + "\n" == evidence_text()


def test_readmes_name_every_number():
    # From kit v1.12 the READMEs write "Blog #N" and "log #N" (ログ#N).
    r = run("--scan", os.path.join(ROOT, "README.md"), os.path.join(ROOT, "README_ja.md"))
    assert r.returncode == 0, r.stdout
