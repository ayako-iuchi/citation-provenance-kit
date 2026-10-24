#!/usr/bin/env python3
"""elapsed — how much clock time each release spanned, from the commit times. Not effort.

The method paper's §8-1 says the work kept no time record and advises "a duration
field on day one". The kit has had that column since v1.0; in the author's log
after v1.2 (log #45 to log #78) it is never filled. A column a person has to fill
in is a rule, not a mechanism.

What does exist is the time of every commit. This tool reads them and reports, for
each tagged release, the commits since the previous tag: how many, the time of the
first and of the tagged commit, and the clock time between. That is elapsed time.
It is not effort: it does not separate work from waiting, does not know about work
done before the first commit or outside git (reading, writing the post, the
author's review), and counts parallel work once. Commit times can also be set by
hand, and are rewritten by a rebase. Read the numbers as grade D at best for
anything about effort.

The first release has no previous tag; its span starts at the first commit. A
range can begin with commits that belong to the previous release (a README updated
after it was published); --named counts only the commits whose subject names the
tag ("Kit v1.12: ..."), which is closer to the release's own work and still not
effort.

Usage:
    python3 elapsed.py --git REPO [--tags v1.3 v1.4 ...] [--named] [--dump]
    python3 elapsed.py --from TIMES.tsv [--tags ...] [--named]

    --git    read a repository (runs git; all tags whose names start with v, in
             version order, unless --tags names some)
    --named  count only commits whose subject names the tag (v1.12, not v1.120)
    --dump   print the commit times the report rests on, as TSV, instead of the
             report: tag, commit, committer time (ISO 8601), subject. Saved, the dump lets
             the report be reproduced without the repository
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
    return [int(n) for n in nums] or [0]


def _git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise ValueError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def from_git(repo, tags=None):
    """[(tag, commit, iso_time)] for every commit in each tag's range, oldest first."""
    all_tags = [t for t in _git(repo, "tag", "--list", "v*").split() if t]
    all_tags.sort(key=_version_key)
    wanted = tags or all_tags
    for t in wanted:
        if t not in all_tags:
            raise ValueError(f"no tag {t}")
    rows = []
    for t in wanted:
        i = all_tags.index(t)
        rng = f"{all_tags[i - 1]}..{t}" if i > 0 else t
        out = _git(repo, "log", "--reverse", "--format=%h\t%cI\t%s", rng)
        for line in out.splitlines():
            commit, when, subject = line.split("\t", 2)
            rows.append((t, commit, when, subject.replace("\t", " ")))
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
    """Does the subject name this tag? v1.12 matches "Kit v1.12:" but not v1.120 or v1.1."""
    return re.search(r"(?<![\w.])" + re.escape(tag) + r"(?![\w]|\.\d)", subject) is not None


def spans(rows, tags=None, named=False):
    """[{tag, commits, first, last, minutes}] in the order the tags first appear."""
    by = {}
    for tag, commit, when, subject in rows:
        t = _time(when)
        by.setdefault(tag, [])
        if not named or names(tag, subject):
            by[tag].append((t, commit, when))
    order = tags or list(by)
    out = []
    for tag in order:
        if tag not in by:
            raise ValueError(f"no commits recorded for {tag}")
        cs = by[tag]
        if not cs:
            out.append({"tag": tag, "commits": 0, "first": None, "first_commit": None,
                        "last": None, "last_commit": None, "minutes": None})
            continue
        first = min(cs)
        last = cs[-1]  # the tagged commit is the last in the range
        out.append({"tag": tag, "commits": len(cs), "first": first[2], "first_commit": first[1],
                    "last": last[2], "last_commit": last[1],
                    "minutes": round((last[0] - first[0]).total_seconds() / 60)})
    return out


def _hm(m):
    sign = "-" if m < 0 else ""
    m = abs(m)
    return f"{sign}{m // 60}h{m % 60:02d}"


def render(sp):
    lines = [NOTE, "", f"{'tag':<8} {'commits':>7}  {'first commit':<26} {'tagged commit':<26} {'elapsed':>8}"]
    for s in sp:
        if not s["commits"]:
            lines.append(f"{s['tag']:<8} {0:>7}  (no commit names this tag)")
            continue
        lines.append(f"{s['tag']:<8} {s['commits']:>7}  {s['first'][:19] + ' ' + s['first_commit']:<26} "
                     f"{s['last'][:19] + ' ' + s['last_commit']:<26} {_hm(s['minutes']):>8}")
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
        if a.git:
            rows = from_git(a.git, a.tags)
        else:
            rows = from_tsv(a.tsv)
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
