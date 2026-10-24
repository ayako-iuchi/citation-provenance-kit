"""Tests for tools/silentcheck.py (kit v1.15)."""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import silentcheck  # noqa: E402

ENV = {**os.environ, "GIT_AUTHOR_NAME": "a", "GIT_AUTHOR_EMAIL": "a@x", "GIT_COMMITTER_NAME": "a", "GIT_COMMITTER_EMAIL": "a@x"}
ALIASES = {"README.md": ["README", "READMEs"], "README_ja.md": ["README", "READMEs"], "kit/book.xlsx": ["workbook"]}


@pytest.mark.parametrize("path,text,want", [
    ("tools/idcheck.py", "Added `tools/idcheck.py`.", "path"),
    ("tools/idcheck.py", "idcheck.py now reads ...", "file name"),
    ("tools/idcheck.py", "idcheck.pyc", None),
    ("tools/idcheck.py", "tools/idcheck.py2", None),
    ("examples/es/lines.json", "Added `examples/es/` with the chapter.", "directory examples/es/"),
    ("examples/es/lines.json", "examples/es/other.json changed", None),
    ("register/namespaces.json", "Added `register/deferred.jsonl`.", None),
    ("README.md", "Both READMEs now say so.", "alias READMEs"),
    ("README_ja.md", "The readme gains a section.", "alias README"),
    ("kit/book.xlsx", "The workbook was regenerated.", "alias workbook"),
    ("kit/book.xlsx", "workbooks", None),
    ("CITATION.cff", "The release commit writes the date.", None),
    # An alias is a word on its own, not part of another path (review of v1.15).
    ("README.md", "Added `examples/x/README.md`.", None),
    ("README.md", "README_ja.md gains a row.", None),
    ("README.md", "See the README.", "alias README"),
    # A directory at the end of a sentence.
    ("examples/es/lines.json", "Added examples/es/.", "directory examples/es/"),
])
def test_named(path, text, want):
    assert silentcheck.named(path, text, ALIASES) == want


def _repo(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()

    def git(*a):
        subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, env=ENV)

    def commit(files, msg, tag=None):
        for name, body in files.items():
            p = repo / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body)
            git("add", name)
        git("commit", "-q", "-m", msg)
        if tag:
            git("tag", tag)
    git("init", "-q")
    commit({"CHANGELOG.md": "# Changelog\n", "a.py": "1", "CITATION.cff": "version: 1.0\n"}, "v1.0", "v1.0")
    commit({"CHANGELOG.md": "# Changelog\n\n## v1.1\n- `a.py` reads more.\n", "a.py": "2", "CITATION.cff": "version: 1.1\n"}, "v1.1", "v1.1")
    commit({"CHANGELOG.md": "# Changelog\n\n## v1.2\n- Nothing new.\n\n## v1.1\n- `a.py` reads more.\n", "b.py": "x"}, "v1.2", "v1.2")
    return repo


def test_ranges_on_a_repository(tmp_path, capsys):
    repo = _repo(tmp_path)
    r = silentcheck.check_range(str(repo), "v1.0", "v1.1")
    assert r["unnamed"] == ["CITATION.cff"]
    r = silentcheck.check_range(str(repo), "v1.1", "v1.2")
    assert r["unnamed"] == ["b.py"]
    assert silentcheck.main(["--git", str(repo)]) == 1
    out = capsys.readouterr().out
    assert "v1.0..v1.1: 2 file(s) changed, 1 not named: CITATION.cff" in out
    assert silentcheck.main(["--git", str(repo), "--from", "v1.0", "--to", "v1.1", "--json"]) == 1


def test_a_changelog_line_added_later_counts(tmp_path):
    # Lines added anywhere in the changelog within the range count, including old sections.
    repo = _repo(tmp_path)
    r = silentcheck.check_range(str(repo), "v1.0", "v1.2")
    assert "b.py" in r["unnamed"] and "a.py" not in r["unnamed"]
    (repo / "CHANGELOG.md").write_text("# Changelog\n\n## v1.2\n- Nothing new.\n\n## v1.1\n- `a.py` reads more.\n- `c.py` added.\n")
    (repo / "c.py").write_text("c")
    _git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, env=ENV)
    _git("add", "-A")
    _git("commit", "-q", "-m", "old section")
    r = silentcheck.check_range(str(repo), "v1.2", "HEAD")
    assert r["unnamed"] == []


def _commit(repo, files, msg, tag=None):
    for name, body in files.items():
        p = repo / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True, env=ENV)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", msg], check=True, capture_output=True, env=ENV)
    if tag:
        subprocess.run(["git", "-C", str(repo), "tag", tag], check=True, capture_output=True, env=ENV)


def test_headings_do_not_name_but_numbered_lines_do(tmp_path):
    repo = _repo(tmp_path)
    _commit(repo, {"CHANGELOG.md": "# Changelog\n\n## c.py update\n#83 d.py changed\n", "c.py": "1", "d.py": "1"}, "h")
    r = silentcheck.check_range(str(repo), "v1.2", "HEAD")
    assert r["unnamed"] == ["c.py"]


def test_pre_release_tags_are_left_out(tmp_path):
    repo = _repo(tmp_path)
    _commit(repo, {"CHANGELOG.md": "# Changelog\n- `e.py`\n", "e.py": "1"}, "rc", "v1.3-rc1")
    assert silentcheck.release_tags(str(repo)) == ["v1.0", "v1.1", "v1.2"]


def test_missing_changelog_exits_2(tmp_path):
    repo = _repo(tmp_path)
    assert silentcheck.main(["--git", str(repo), "--changelog", "CHANGES.md"]) == 2


def test_colour_and_odd_file_names(tmp_path):
    repo = _repo(tmp_path)
    subprocess.run(["git", "-C", str(repo), "config", "color.ui", "always"], check=True, env=ENV)
    subprocess.run(["git", "-C", str(repo), "config", "color.diff", "always"], check=True, env=ENV)
    _commit(repo, {"CHANGELOG.md": "# Changelog\n- `x\ty.py` and `q\"z.py` and `ü.py`\n",
                   "x\ty.py": "1", 'q"z.py': "1", "ü.py": "1", "other.py": "1"}, "odd")
    r = silentcheck.check_range(str(repo), "v1.2", "HEAD")
    assert r["unnamed"] == ["other.py"]


def test_json_output(tmp_path, capsys):
    repo = _repo(tmp_path)
    assert silentcheck.main(["--git", str(repo), "--from", "v1.0", "--to", "v1.1", "--json"]) == 1
    d = json.loads(capsys.readouterr().out)
    assert d[0]["from"] == "v1.0" and d[0]["unnamed"] == ["CITATION.cff"]
    assert {f["path"]: f["named_by"] for f in d[0]["files"]} == {"CITATION.cff": None, "a.py": "path"}


@pytest.mark.parametrize("args", [["--from", "v1.0"], ["--from", "v9", "--to", "v1.1"]])
def test_bad_arguments_exit_2(tmp_path, args, capsys):
    repo = _repo(tmp_path)
    assert silentcheck.main(["--git", str(repo), *args]) == 2


@pytest.mark.parametrize("content", ["[1]", '{"a": "b"}', '{"a": [""]}', "not json"])
def test_bad_aliases_exit_2(tmp_path, content):
    repo = _repo(tmp_path)
    p = tmp_path / "al.json"
    p.write_text(content)
    assert silentcheck.main(["--git", str(repo), "--aliases", str(p)]) == 2


def test_kit_aliases_file_is_valid():
    d = silentcheck.load_aliases(os.path.join(ROOT, "register", "silent_aliases.json"))
    assert set(d) >= {"README.md", "README_ja.md", "kit/citation-provenance-kit.xlsx"}


def test_evidence_reproduces():
    stored = open(os.path.join(ROOT, "evidence", "silentcheck_2026-10-24.txt"), encoding="utf-8").read()
    for block in stored.split("\n\n$ ")[1:]:
        cmd, _, want = block.partition("\n")
        args = cmd.split()
        if args[0] == "python3":
            args[0] = sys.executable
        try:
            r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
        except OSError:
            pytest.skip("git not available")
        if r.returncode == 2 and "unknown revision" in r.stderr:
            pytest.skip("tags not fetched")
        got = r.stdout.rstrip("\n") + (f"\n[exit {r.returncode}]" if r.returncode else "")
        assert got == want.rstrip("\n"), cmd


def test_this_release_names_every_changed_file():
    """The kit's own release, against the latest tag before it: nothing changed silently."""
    # Only tags reachable from HEAD: a checkout of an older release compares with the tag before it,
    # not with a later one (review of v1.15).
    try:
        tags = silentcheck.release_tags(ROOT, merged="HEAD")
        head_tags = silentcheck._git(ROOT, "tag", "--points-at", "HEAD").split()
    except ValueError:
        pytest.skip("not a git checkout")
    base = [t for t in tags if t not in head_tags]
    if not base:
        pytest.skip("no earlier tag")
    aliases = silentcheck.load_aliases(os.path.join(ROOT, "register", "silent_aliases.json"))
    try:
        r = silentcheck.check_range(ROOT, base[-1], "HEAD", aliases=aliases)
    except ValueError:
        pytest.skip("tags not fetched")
    assert r["unnamed"] == [], r["unnamed"]
