#!/usr/bin/env python3
"""elapsed — how much clock time each release spanned, from the commit times. Not effort.

The method paper's §8-1 says the work kept no time record and advises "a duration
field on day one". The kit has had that column since v1.0; in the author's log
after v1.2 (log #45 to log #78) it is never filled. A column a person has to fill
in is a rule, not a mechanism.

What does exist is the time of every commit. This tool reads them and reports, for
each tag, the commits that belong to it — reachable from the tag and from no tag
on an earlier commit in its history — how many there are, the time of the first
and of the tagged commit, and the clock time between. That is elapsed time. It is
not effort: it does not separate work from waiting, does not know about work done
before the first commit or outside git (reading, writing the post, the author's
review), and counts parallel work once. Commit times can also be set by hand, and
are rewritten by a rebase. Read the numbers as grade D at best for anything about
effort. Tags carry no time of their own here: a span ends at the tagged commit, not
at the moment the tag was made.

The first tag in a history has no earlier tag; its span starts at the first
commit. Two tags on the same commit share one range: the first in version order
gets it, and the other is reported as pointing at the same commit. A range can
begin with commits that belong to the release before (a README updated after it
was published); --named starts the span at the first commit whose subject names
the tag ("Kit v1.12: ...", not "kit-v1.12" or "v1.12-rc1"), which is closer to the
release's own work and still not effort. The span still ends at the tagged commit.

Usage:
    python3 elapsed.py --git REPO [--tags v1.3 v1.4 ...] [--named] [--dump]
    python3 elapsed.py --from TIMES.tsv [--tags ...] [--named]

    --git    read a repository (runs git; all tags whose names start with v, in
             version order, unless --tags names some). A shallow clone is refused.
    --named  start each span at the first commit whose subject names the tag
    --dump   print the commit times the report rests on, as TSV, instead of the
             report: tag, commit, committer time (ISO 8601), subject; every commit
             of each range, so that --named can be applied when the dump is read.
             A tag on the same commit as another is written with "-" for commit
             and time. Saved, the dump lets the report be reproduced without the
             repository.
    --from   read such a dump

Exit status: 0, or 2 on unreadable input.

Standard library only (git is needed only for --git). CC0 1.0. Part of the
citation provenance kit (v1.13).
"""
import argparse
import datetime as dt
import re
import subprocess
import sys

NOTE = "Elapsed clock time between commits. Not effort: waiting, parallel work and work outside git are not separated."


def _version_key(tag):
    nums = re.findall(r"\d+", tag)
    return ([int(n) for n in nums] or [0], tag)


def _git(repo, *args, ok=(0,)):
    try:
        r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    except OSError as e:
        raise ValueError(f"git: {e}") from None
    if r.returncode not in ok:
        raise ValueError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r


def _unique(seq):
    return list(dict.fromkeys(seq))


def from_git(repo, tags=None):
    """[(tag, commit, iso_time, subject)] for every commit in each tag's range, oldest first."""
    if _git(repo, "rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        raise ValueError(f"{repo} is a shallow clone; fetch the full history first")
    all_tags = sorted((t for t in _git(repo, "tag", "--list", "v*").stdout.split() if t), key=_version_key)
    wanted = _unique(tags) if tags else all_tags
    for t in wanted:
        if t not in all_tags:
            raise ValueError(f"no tag {t}")
    commit = {t: _git(repo, "rev-parse", f"{t}^{{commit}}").stdout.strip() for t in all_tags}

    def ancestor(a, b):
        return _git(repo, "merge-base", "--is-ancestor", a, b, ok=(0, 1)).returncode == 0

    rows = []
    for t in wanted:
        same = [u for u in all_tags if commit[u] == commit[t]]
        if same[0] != t:
            rows.append((t, "-", "-", f"same commit as {same[0]}"))
            continue
        earlier = [commit[u] for u in all_tags if commit[u] != commit[t] and ancestor(commit[u], commit[t])]
        out = _git(repo, "log", "--reverse", "--format=%h%x09%cI%x09%s", commit[t], *("^" + c for c in _unique(earlier))).stdout
        for line in out.splitlines():
            c, when, subject = line.split("\t", 2)
            rows.append((t, c, when, subject.replace("\t", " ")))
    return rows


def from_tsv(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t", 3)
            if len(parts) != 4:
                raise ValueError(f"line {n}: expected tag, commit, time and subject separated by tabs")
            rows.append(tuple(parts))
    return rows


def _time(s):
    try:
        t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"{s!r} is not an ISO 8601 time") from None
    if t.tzinfo is None:
        raise ValueError(f"{s!r} has no time zone")
    return t


def names(tag, subject):
    """Does the subject name this tag? "Kit v1.12:" names v1.12; "v1.120", "v1.12.1",
    "v1.12-rc1" and "kit-v1.12" do not."""
    return re.search(r"(?<![\w.\-/])" + re.escape(tag) + r"(?![\w]|\.\d|-\w)", subject) is not None


def spans(rows, tags=None, named=False):
    """[{tag, commits, first, first_commit, last, last_commit, minutes, note}] in the order given."""
    by, notes = {}, {}
    for tag, commit, when, subject in rows:
        by.setdefault(tag, [])
        if commit == "-":
            notes[tag] = subject
            continue
        by[tag].append((_time(when), commit, when, subject))
    order = _unique(tags) if tags else list(by)
    out = []
    for tag in order:
        if tag not in by:
            raise ValueError(f"no commits recorded for {tag}")
        cs = by[tag]
        row = {"tag": tag, "commits": 0, "first": None, "first_commit": None, "last": None, "last_commit": None,
               "minutes": None, "note": notes.get(tag)}
        if cs:
            last = cs[-1]  # the tagged commit is the last in the range
            row.update(last=last[2], last_commit=last[1])
            pool = [c for c in cs if names(tag, c[3])] if named else cs
            if pool:
                first = min(pool, key=lambda c: c[0])
                row.update(commits=len(pool), first=first[2], first_commit=first[1],
                           minutes=round((last[0] - first[0]).total_seconds() / 60))
            elif not row["note"]:
                row["note"] = "no commit names this tag"
        out.append(row)
    return out


def _hm(m):
    sign = "-" if m < 0 else ""
    m = abs(m)
    return f"{sign}{m // 60}h{m % 60:02d}"


def render(sp):
    w = 33
    lines = [NOTE, "", f"{'tag':<8} {'commits':>7}  {'first commit':<{w}} {'tagged commit':<{w}} {'elapsed':>8}"]
    for s in sp:
        if s["minutes"] is None:
            lines.append(f"{s['tag']:<8} {s['commits']:>7}  ({s['note']})")
            continue
        lines.append(f"{s['tag']:<8} {s['commits']:>7}  {s['first'] + ' ' + s['first_commit']:<{w}} "
                     f"{s['last'] + ' ' + s['last_commit']:<{w}} {_hm(s['minutes']):>8}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--git", metavar="REPO")
    src.add_argument("--from", dest="tsv", metavar="TIMES.tsv")
    ap.add_argument("--tags", nargs="+")
    ap.add_argument("--named", action="store_true")
    ap.add_argument("--dump", action="store_true")
    a = ap.parse_args(argv)
    try:
        rows = from_git(a.git, a.tags) if a.git else from_tsv(a.tsv)
        if a.dump:
            print("# tag\tcommit\tcommitter time\tsubject. " + NOTE)
            for r in rows:
                print("\t".join(r))
            return 0
        print(render(spans(rows, a.tags, a.named)))
    except (OSError, UnicodeDecodeError, ValueError) as e:
        print(f"elapsed: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
