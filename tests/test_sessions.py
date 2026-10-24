"""Tests for tools/sessions.py (kit v1.14)."""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import sessions  # noqa: E402

COMMITS = os.path.join(ROOT, "evidence", "sessions_commits_2026-10-24.tsv")
ENV = {**os.environ, "GIT_AUTHOR_NAME": "a", "GIT_AUTHOR_EMAIL": "a@x", "GIT_COMMITTER_NAME": "a", "GIT_COMMITTER_EMAIL": "a@x"}


def R(c, when, session, files, parents=(), subject="s"):
    return (c, list(parents), when, session, list(files), subject)


def test_overlap_on_diverged_lines_is_reported():
    rows = [R("a1", "2026-10-12T19:00:00+09:00", "A", ["README.md"]),
            R("b1", "2026-10-12T20:00:00+09:00", "B", ["README.md"], ["a1"]),   # made on top of a1: saw it
            R("a2", "2026-10-13T10:37:00+09:00", "A", ["README.md"], ["a1"]),   # main
            R("b2", "2026-10-13T10:45:00+09:00", "B", ["README.md"], ["b1"])]   # branch
    res = sessions.analyse(rows)
    [c] = res["concurrent"]
    pairs = [(p["first"]["commit"], p["second"]["commit"]) for p in c["same_file"]]
    assert ("a2", "b2") in pairs and ("a1", "b1") not in pairs
    assert ("b1", "a2") in pairs  # b1 on the branch, a2 on main: neither saw the other


def test_no_overlap_is_a_handoff():
    rows = [R("a1", "2026-10-23T10:00:00+09:00", "A", ["CHANGELOG.md"]),
            R("b1", "2026-10-23T10:20:00+09:00", "B", ["CHANGELOG.md"], ["a1"])]
    res = sessions.analyse(rows)
    assert res["concurrent"] == [] and res["handoffs"][0]["minutes"] == 20


def test_overlap_without_shared_files():
    rows = [R("a1", "2026-10-01T10:00:00+09:00", "A", ["x"]), R("b1", "2026-10-01T10:30:00+09:00", "B", ["y"]),
            R("a2", "2026-10-01T11:00:00+09:00", "A", ["x"], ["a1"])]
    res = sessions.analyse(rows)
    assert res["concurrent"][0]["same_file"] == []
    assert "no file changed by both" in sessions.render(res)


def test_unsigned_commits_and_exit(tmp_path, capsys):
    p = tmp_path / "c.tsv"
    p.write_text("x1\t\t2026-10-01T10:00:00+09:00\t\tf\tno trailer\n", encoding="utf-8")
    assert sessions.main(["--from", str(p)]) == 1
    assert "no trailer" in capsys.readouterr().out


@pytest.mark.parametrize("content", ["x1\t2026\n", "x1\t\tyesterday\tA\tf\ts\n", "x1\t\t2026-10-01T10:00:00\tA\tf\ts\n"])
def test_bad_input_exits_2(tmp_path, content):
    p = tmp_path / "c.tsv"
    p.write_text(content, encoding="utf-8")
    assert sessions.main(["--from", str(p)]) == 2


def test_long_history_does_not_recurse():
    rows = [R("c0", "2026-10-01T00:00:00+00:00", "A", ["f"])]
    for i in range(1, 3000):
        rows.append(R(f"c{i}", f"2026-10-01T{(i // 3600) % 24:02d}:{(i // 60) % 60:02d}:{i % 60:02d}+00:00", "A", ["f"], [f"c{i - 1}"]))
    rows.append(R("b", "2026-10-01T00:30:00+00:00", "B", ["f"], ["c0"]))
    res = sessions.analyse(rows)
    assert res["concurrent"][0]["same_file"]


def test_from_git(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()

    def git(*a, when=None):
        e = dict(ENV)
        if when:
            e["GIT_COMMITTER_DATE"] = e["GIT_AUTHOR_DATE"] = when
        return subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True, env=e)
    git("init", "-q", "-b", "main")

    def commit(msg, session, when):
        (repo / "README.md").write_text(msg)
        git("add", "README.md")
        body = msg + (f"\n\nClaude-Session: https://claude.ai/code/{session}" if session else "")
        git("commit", "-q", "-m", body, when=when)
    commit("one", "s_A", "2026-10-12T19:00:00+09:00")
    git("checkout", "-q", "-b", "kit")
    commit("two", "s_B", "2026-10-12T20:00:00+09:00")
    git("checkout", "-q", "main")
    commit("three", "s_A", "2026-10-13T10:37:00+09:00")
    git("checkout", "-q", "kit")
    commit("four", "s_B", "2026-10-13T10:45:00+09:00")
    commit("five", None, "2026-10-13T11:00:00+09:00")
    res = sessions.analyse(sessions.from_git(str(repo)))
    assert [sessions.short(s["session"]) for s in res["sessions"]] == ["s_A", "s_B"]
    assert len(res["unsigned"]) == 1
    assert any(p["minutes"] == 8 for p in res["concurrent"][0]["same_file"])
    assert sessions.main(["--git", str(repo)]) == 1


def test_evidence_reproduces():
    stored = open(os.path.join(ROOT, "evidence", "sessions_2026-10-24.txt"), encoding="utf-8").read()
    for block in stored.split("\n\n$ ")[1:]:
        cmd, _, want = block.partition("\n")
        args = cmd.split()
        if args[0] == "python3":
            args[0] = sys.executable
        r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
        got = r.stdout.rstrip("\n") + (f"\n[exit {r.returncode}]" if r.returncode else "")
        assert got == want.rstrip("\n"), cmd


def test_the_kit_history_shows_the_13_october_pair():
    res = sessions.analyse(sessions.from_tsv(COMMITS))
    pairs = [(p["first"]["commit"], p["second"]["commit"], p["minutes"]) for c in res["concurrent"] for p in c["same_file"]]
    assert ("c9a9823", "fdd8f9c", 8) in pairs
    import datetime as _dt
    assert all(not c["same_file"] for c in res["concurrent"] if c["from"] > _dt.datetime(2026, 10, 14, tzinfo=_dt.timezone.utc))


# --- review of eaa4fe4 (2026-10-24) -------------------------------------------

def test_several_sessions_in_one_trailer():
    rows = [R("a1", "2026-10-01T10:00:00+09:00", "A", ["x"]), R("ac", "2026-10-01T11:00:00+09:00", "A, C", ["y"], ["a1"]),
            R("c1", "2026-10-01T12:00:00+09:00", "C", ["z"], ["ac"])]
    res = sessions.analyse(rows)
    counts = {s["session"]: s["commits"] for s in res["sessions"]}
    assert counts == {"A": 2, "C": 2} and res["unsigned"] == []


@pytest.mark.parametrize("rows,needle", [
    ([R("a", "2026-10-01T10:00:00+09:00", "A", ["x"]), R("a", "2026-10-01T11:00:00+09:00", "A", ["x"])], "twice"),
    ([R("a", "2026-10-01T10:00:00+09:00", "A", ["x"], ["b"]), R("b", "2026-10-01T11:00:00+09:00", "B", ["x"], ["a"])], "cycle"),
])
def test_inconsistent_input(rows, needle):
    with pytest.raises(ValueError, match=needle):
        sessions.analyse(rows)


def test_missing_parents_are_reported():
    res = sessions.analyse([R("a", "2026-10-01T10:00:00+09:00", "A", ["x"], ["zz"])])
    assert res["missing_parents"] == ["zz"] and "history incomplete" in sessions.render(res)


def test_file_names_round_trip(tmp_path):
    names = ["a|b.md", "c\\d.md", "日本語.md", "@@x"]
    assert sessions.split_files(sessions.join_files(names)) == names


def test_stash_and_merge_files(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()

    def git(*a, when=None):
        e = dict(ENV)
        if when:
            e["GIT_COMMITTER_DATE"] = e["GIT_AUTHOR_DATE"] = when
        return subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True, env=e)

    def commit(f, msg, session, when):
        (repo / f).write_text(msg)
        git("add", f)
        git("commit", "-q", "-m", f"{msg}\n\nClaude-Session: https://claude.ai/code/{session}", when=when)
    git("init", "-q", "-b", "main")
    commit("a.md", "one", "s_A", "2026-10-01T09:00:00+09:00")
    git("checkout", "-q", "-b", "kit")
    commit("b.md", "two", "s_B", "2026-10-01T09:30:00+09:00")
    git("checkout", "-q", "main")
    commit("a.md", "three", "s_A", "2026-10-01T10:00:00+09:00")
    git("checkout", "-q", "kit")
    e = dict(ENV, GIT_COMMITTER_DATE="2026-10-01T10:10:00+09:00", GIT_AUTHOR_DATE="2026-10-01T10:10:00+09:00")
    subprocess.run(["git", "-C", str(repo), "merge", "-q", "--no-edit", "-m", "merge\n\nClaude-Session: https://claude.ai/code/s_B", "main"],
                   check=True, capture_output=True, env=e)
    git("checkout", "-q", "main")
    commit("a.md", "four", "s_A", "2026-10-01T10:20:00+09:00")
    (repo / "a.md").write_text("dirty")
    git("stash", "-q")
    res = sessions.analyse(sessions.from_git(str(repo)))
    assert res["unsigned"] == []                      # the stash is not read
    assert all(not c["same_file"] for c in res["concurrent"])  # a clean merge does not claim main's files
