#!/usr/bin/env python3
"""sessions — who was editing at the same time, read from the commit history.

A log kept open after release finds failures of a kind a closed log never sees.
One of them is two editors at once. On 13 October 2026 two sessions changed the
same lines of the kit's READMEs eight minutes apart, on two branches, one with the
number of a post only and one with its number and title, and one of them wrote
nothing in the changelog (log #48). The response was a rule: one thread at a time
is the sole editor, and a handoff memo says when that changes. A rule is not a
mechanism. This tool reads whether the rule held.

Each commit made in a session carries a trailer naming it (Claude-Session by
default; a trailer naming several sessions counts the commit in each). The tool
reads, for every commit on every branch, tag and remote branch, the time it was
committed, its session and the files it changed (a merge: the files that differ
from every parent, as git's dense combined diff shows them), and reports:

    sessions     each session's first and last commit, and how many
    concurrent   two sessions whose spans (first to last commit) overlap, and the
                 commits of the two that changed the same file on lines of
                 history that had diverged: neither commit had the other in its
                 history, and one was made while the other session was active.
                 Two editors at once, each without the other's change in view.
                 A commit made on top of the other session's commit is not
                 reported: it saw it
    handoffs     a session whose first commit changed a file the previous
                 session's last commit had changed, with the time between: one
                 editor after another, as the rule intends (for information)
    unsigned     commits with no session trailer: nobody can say who made them

A session's span is from its first to its last commit. A session can be open
before its first commit and after its last, and can edit files outside git (the
series' theme list, memo and posts are documents, not files in this repository);
the tool sees neither. Two spans that overlap say that two sessions committed in
the same period, not that they conflicted. A rebase, a cherry-pick or an amended
commit gets a new commit time and new parents: a concurrent edit that was later
rebased looks like a handoff. For each later commit only the nearest earlier
commit of the other session is listed. The comparison is of every pair of commits
in two overlapping sessions, which is fine for a few thousand commits.

Usage:
    python3 sessions.py --git REPO [--trailer Claude-Session] [--dump]
    python3 sessions.py --from COMMITS.tsv

    --dump   print the commits the report rests on, as TSV: commit, parents,
             committer time, session, files (separated by |), subject. Saved, the dump lets
             the report be reproduced without the repository
    --from   read such a dump

Exit status: 0; 1 if two sessions changed the same file on diverged lines of
history, or a commit has no session; 2 on unreadable or inconsistent input (a
commit listed twice, parents that form a cycle).

Standard library only (git is needed only for --git). CC0 1.0. Part of the
citation provenance kit (v1.14).
"""
import argparse
import datetime as dt
import subprocess
import sys


def _time(s):
    try:
        t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"{s!r} is not an ISO 8601 time") from None
    if t.tzinfo is None:
        raise ValueError(f"{s!r} has no time zone")
    return t


def from_git(repo, trailer="Claude-Session"):
    """[(commit, [parents], iso_time, session, [files], subject)], oldest first."""
    try:
        r = subprocess.run(["git", "-C", repo, "rev-parse", "--is-shallow-repository"], capture_output=True, text=True)
    except OSError as e:
        raise ValueError(f"git: {e}") from None
    if r.returncode != 0:
        raise ValueError(f"git: {r.stderr.strip()}")
    if r.stdout.strip() == "true":
        raise ValueError(f"{repo} is a shallow clone; fetch the full history first")
    fmt = f"%x1e%h%x09%p%x09%cI%x09%(trailers:key={trailer},valueonly,separator=%x2C)%x09%s"
    r = subprocess.run(["git", "-C", repo, "-c", "core.quotePath=false", "log", "--branches", "--tags", "--remotes",
                        "--reverse", "--name-only", "--no-renames", "--diff-merges=dense-combined", f"--format={fmt}"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        hint = " (--diff-merges needs git 2.31 or later)" if "diff-merges" in r.stderr else ""
        raise ValueError(f"git log: {r.stderr.strip()}{hint}")
    rows, cur = [], None
    for line in r.stdout.split("\n"):  # not splitlines(): it splits at \x1e too
        if line.startswith("\x1e"):
            commit, parents, when, session, subject = line[1:].split("\t", 4)
            cur = [commit, parents.split(), when, ",".join(x.strip() for x in session.split(",") if x.strip()), [],
                   subject.replace("\t", " ")]
            rows.append(cur)
        elif line.strip() and cur is not None:
            cur[4].append(line.strip())
    return [tuple(x) for x in rows]


def from_tsv(path):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for n, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t", 5)
            if len(parts) != 6:
                raise ValueError(f"line {n}: expected commit, parents, time, session, files and subject separated by tabs")
            commit, parents, when, session, files, subject = parts
            session = ",".join(x.strip() for x in session.split(",") if x.strip())
            rows.append((commit, parents.split(), when, session, [x for x in split_files(files) if x], subject))
    return rows


def join_files(files):
    """Files for the dump: separated by |, with \\ and | escaped."""
    return "|".join(f.replace("\\", "\\\\").replace("|", "\\|") for f in files)


def split_files(s):
    out, cur, esc = [], [], False
    for ch in s:
        if esc:
            cur.append(ch)
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == "|":
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out


def short(session):
    """The last path segment of a session URL, or the value as given."""
    return session.rstrip("/").rsplit("/", 1)[-1] if session else "(none)"


def analyse(rows):
    commits = sorted(({"commit": c, "parents": p, "when": w, "t": _time(w), "session": s,
                       "sessions": [x.strip() for x in s.split(",") if x.strip()], "files": set(f), "subject": sub}
                      for c, p, w, s, f, sub in rows), key=lambda x: x["t"])
    parents = {}
    for c in commits:
        if c["commit"] in parents:
            raise ValueError(f"commit {c['commit']} appears twice")
        parents[c["commit"]] = c["parents"]
    missing = sorted({p for ps in parents.values() for p in ps if p not in parents})
    # a history is acyclic; a cycle in the input would hide every pair it touches
    state = {}
    for start in parents:
        if start in state:
            continue
        stack = [(start, iter(parents[start]))]
        state[start] = 1
        while stack:
            node, it = stack[-1]
            nxt = next((p for p in it if p in parents), None)
            if nxt is None:
                state[node] = 2
                stack.pop()
            elif state.get(nxt) == 1:
                raise ValueError(f"the parents form a cycle at {nxt}")
            elif nxt not in state:
                state[nxt] = 1
                stack.append((nxt, iter(parents[nxt])))
    memo = {}

    def history(h):
        """Every commit reachable from h, h included (iterative; histories can be long)."""
        if h in memo:
            return memo[h]
        seen, stack = set(), [h]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            if x in memo:
                seen |= memo[x]
                continue
            stack.extend(parents.get(x, ()))
        memo[h] = seen
        return seen

    def diverged(x, y):
        return x["commit"] not in history(y["commit"]) and y["commit"] not in history(x["commit"])
    by = {}
    for c in commits:
        for s in c["sessions"]:
            by.setdefault(s, []).append(c)
    sessions = [{"session": s, "commits": len(cs), "first": cs[0], "last": cs[-1]} for s, cs in by.items()]
    sessions.sort(key=lambda s: s["first"]["t"])
    concurrent = []
    for i, a in enumerate(sessions):
        for b in sessions[i + 1:]:
            start, end = max(a["first"]["t"], b["first"]["t"]), min(a["last"]["t"], b["last"]["t"])
            if start <= end:
                def active(c, s):
                    return s["first"]["t"] <= c["t"] <= s["last"]["t"]
                pairs = {}
                for x in by[a["session"]]:
                    for y in by[b["session"]]:
                        if x is y:
                            continue
                        common = tuple(sorted(x["files"] & y["files"]))
                        if common and (active(x, b) or active(y, a)) and diverged(x, y):
                            (first, fs), (second, ss) = sorted(((x, a["session"]), (y, b["session"])), key=lambda c: c[0]["t"])
                            gap = (second["t"] - first["t"]).total_seconds()
                            key = (second["commit"], common)
                            if key not in pairs or gap < pairs[key]["gap"]:
                                pairs[key] = {"first": first, "second": second, "first_session": fs, "second_session": ss,
                                              "files": list(common), "gap": gap, "minutes": round(gap / 60)}
                same = sorted(pairs.values(), key=lambda p: (p["second"]["t"], p["first"]["t"]))
                concurrent.append({"a": a["session"], "b": b["session"], "from": start, "to": end, "same_file": same})
    handoffs = []
    for prev, nxt in zip(sessions, sessions[1:]):
        if nxt["first"]["t"] > prev["last"]["t"]:
            common = sorted(prev["last"]["files"] & nxt["first"]["files"])
            if common:
                handoffs.append({"from": prev["session"], "to": nxt["session"], "files": common,
                                 "after": prev["last"], "first": nxt["first"],
                                 "minutes": round((nxt["first"]["t"] - prev["last"]["t"]).total_seconds() / 60)})
    unsigned = [c for c in commits if not c["sessions"]]
    return {"commits": commits, "sessions": sessions, "concurrent": concurrent, "handoffs": handoffs, "unsigned": unsigned,
            "missing_parents": missing}


def _ts(c):
    return f"{c['when']} {c['commit']}"


def render(a):
    out = [f"{len(a['commits'])} commit(s), {len(a['sessions'])} session(s). A span is first to last commit; "
           "a session can be open before and after it, and edit outside git."]
    if a["missing_parents"]:
        out.append(f"history incomplete: {len(a['missing_parents'])} parent(s) not in the input; "
                   "commits whose parents are missing are read as roots")
    out += ["", "sessions"]
    for s in a["sessions"]:
        out.append(f"  {short(s['session'])}  {s['commits']:>3} commit(s)  {_ts(s['first'])}  to  {_ts(s['last'])}")
    out += ["", "concurrent"]
    if not a["concurrent"]:
        out.append("  none")
    for c in a["concurrent"]:
        out.append(f"  {short(c['a'])} and {short(c['b'])} overlap from {c['from'].isoformat()} to {c['to'].isoformat()}")
        if not c["same_file"]:
            out.append("    no file changed by both on diverged lines of history")
        for p in c["same_file"]:
            out.append(f"    same file: {', '.join(p['files'])}: {p['first']['commit']} ({short(p['first_session'])}, "
                       f"{p['first']['when']}) then {p['second']['commit']} ({short(p['second_session'])}, "
                       f"{p['minutes']} min later)")
    out += ["", "handoffs (for information)"]
    if not a["handoffs"]:
        out.append("  none")
    for h in a["handoffs"]:
        out.append(f"  {short(h['from'])} -> {short(h['to'])} after {h['minutes']} min: {', '.join(h['files'])} "
                   f"({h['after']['commit']} then {h['first']['commit']})")
    out += ["", "unsigned"]
    out.append("  none" if not a["unsigned"] else "")
    for c in a["unsigned"]:
        out.append(f"  {_ts(c)}  {c['subject']}")
    return "\n".join(x for x in out if x != "")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--git", metavar="REPO")
    src.add_argument("--from", dest="tsv", metavar="COMMITS.tsv")
    ap.add_argument("--trailer", default="Claude-Session")
    ap.add_argument("--dump", action="store_true")
    a = ap.parse_args(argv)
    try:
        rows = from_git(a.git, a.trailer) if a.git else from_tsv(a.tsv)
        if a.dump:
            print(f"# commit\tparents\tcommitter time\t{a.trailer}\tfiles\tsubject")
            for c, p, w, s, f, sub in rows:
                print("\t".join([c, " ".join(p), w, s, join_files(f), sub]))
            return 0
        res = analyse(rows)
    except (OSError, UnicodeDecodeError, ValueError) as e:
        print(f"sessions: {e}", file=sys.stderr)
        return 2
    print(render(res))
    return 1 if res["unsigned"] or any(c["same_file"] for c in res["concurrent"]) else 0


if __name__ == "__main__":
    sys.exit(main())
