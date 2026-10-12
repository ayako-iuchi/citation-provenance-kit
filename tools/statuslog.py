#!/usr/bin/env python3
"""statuslog — an append-only log of status assertions, and two questions it can answer.

The kit v1.1 register keeps one value and one "last resolved" date per row. When a
value moves, the row has nowhere to keep the old one. This log keeps every
assertion and never edits one, so it can answer two different questions:

    believed_on   What had I recorded about this, as of day X?   (transaction time)
    current       What may I rely on today?                      (expiry applied)

`current` returns no value, rather than an old one, when the assertion has
expired. An expired value is the one most likely to be quoted with confidence.

Usage:
    python3 statuslog.py LOG --subject S --component C --on YYYY-MM-DD [--believed]
    python3 statuslog.py LOG --list
    python3 statuslog.py --verify-append OLD NEW

    --believed       answer "what had I recorded as of that day" instead of
                     "what may I rely on that day"
    --verify-append  check that NEW only adds lines to OLD (exit 1 if any line of
                     OLD was changed or removed)

The log is JSON Lines: one assertion per line, in the order recorded. The shape of
a line is schema/status_assertion.schema.json. Standard library only. CC0 1.0.
Part of the citation provenance kit.
"""
import argparse
import datetime as dt
import json
import sys


def load(path):
    """Read a JSON Lines log. Blank lines are ignored."""
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _day(s):
    return dt.date.fromisoformat(s)


def check(log):
    """Return a list of problems with the log as a whole (empty if none)."""
    problems = []
    ids = set()
    for n, a in enumerate(log, start=1):
        if a["id"] in ids:
            problems.append(f"line {n}: id {a['id']} is used twice")
        if a.get("supersedes") and a["supersedes"] not in ids:
            problems.append(f"line {n}: supersedes {a['supersedes']}, which is not recorded earlier in the log")
        ids.add(a["id"])
    return problems


def believed_on(log, subject, component, day):
    """The latest assertion about (subject, component) recorded on or before `day`.

    Returns the assertion as recorded, or None if nothing had been recorded by then.
    When two assertions share a recording day, the later line wins.
    """
    day = _day(day) if isinstance(day, str) else day
    best = None
    for a in log:
        if a["subject"] == subject and a["component"] == component and _day(a["recorded_on"]) <= day:
            if best is None or _day(a["recorded_on"]) >= _day(best["recorded_on"]):
                best = a
    return best


def current(log, subject, component, today):
    """What may be relied on `today`.

    Returns a dict:
        value      the value, or None
        status     "ok", "no-expiry-stated", "expired" or "no-record"
        assertion  the assertion the answer rests on, or None
    An expired assertion yields value None. It is not replaced by the old value.
    """
    today = _day(today) if isinstance(today, str) else today
    a = believed_on(log, subject, component, today)
    if a is None:
        return {"value": None, "status": "no-record", "assertion": None}
    if a.get("expires_on") is None:
        return {"value": a["value"], "status": "no-expiry-stated", "assertion": a}
    if today > _day(a["expires_on"]):
        return {"value": None, "status": "expired", "assertion": a}
    return {"value": a["value"], "status": "ok", "assertion": a}


def verify_append(old_path, new_path):
    """True if every line of OLD appears unchanged, in order, at the start of NEW."""
    with open(old_path, encoding="utf-8") as f:
        old = [l.rstrip("\n") for l in f if l.strip()]
    with open(new_path, encoding="utf-8") as f:
        new = [l.rstrip("\n") for l in f if l.strip()]
    return new[: len(old)] == old


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("log", nargs="?")
    p.add_argument("--subject")
    p.add_argument("--component")
    p.add_argument("--on", help="YYYY-MM-DD")
    p.add_argument("--believed", action="store_true")
    p.add_argument("--list", action="store_true")
    p.add_argument("--verify-append", nargs=2, metavar=("OLD", "NEW"))
    args = p.parse_args(argv)

    if args.verify_append:
        ok = verify_append(*args.verify_append)
        print("append-only: yes" if ok else "append-only: NO — a recorded line was changed or removed")
        return 0 if ok else 1

    log = load(args.log)
    problems = check(log)
    for msg in problems:
        print("problem:", msg, file=sys.stderr)

    if args.list:
        for a in log:
            print(f"{a['recorded_on']}  {a['id']:<10} {a['component']:<13} {a['subject']}")
        return 1 if problems else 0

    if args.believed:
        a = believed_on(log, args.subject, args.component, args.on)
        print(json.dumps(a, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(current(log, args.subject, args.component, args.on), ensure_ascii=False, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
