#!/usr/bin/env python3
"""migrate_register — turn a kit v1.1 register (CSV) into the first lines of a status log.

Each register row becomes one assertion, recorded on its "Last resolved" date.
Nothing is invented. In particular, an expiry date is set only where the
"Next check" text names a date or a regular interval:

    "2027-01"                  -> 2027-01-01
    "November 2026"            -> 2026-11-01
    "Monthly ..."              -> one month after Last resolved
    "Each June–July"           -> 1 June of the next year after Last resolved
                                  (1 June of the same year if that is still ahead)
    anything else              -> null, and the original text is kept in next_check

A null expiry is reported by statuslog.py as "no-expiry-stated", not treated as
permanent. Rows that cannot be parsed are listed on stderr.

Usage:
    python3 migrate_register.py REGISTER.csv > status_log.jsonl

Standard library only. CC0 1.0. Part of the citation provenance kit.
"""
import csv
import datetime as dt
import json
import re
import sys

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}


def add_month(d):
    y, m = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    return d.replace(year=y, month=m, day=min(d.day, 28))


def expiry(next_check, resolved):
    t = next_check.strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})", t)
    if m:
        return dt.date(int(m[1]), int(m[2]), 1)
    m = re.fullmatch(r"([A-Z][a-z]+) (\d{4})", t)
    if m and m[1] in MONTHS:
        return dt.date(int(m[2]), MONTHS[m[1]], 1)
    if t.startswith("Monthly"):
        return add_month(resolved)
    m = re.fullmatch(r"Each ([A-Z][a-z]+)[–-][A-Z][a-z]+", t)
    if m and m[1] in MONTHS:
        d = dt.date(resolved.year, MONTHS[m[1]], 1)
        return d if d > resolved else d.replace(year=resolved.year + 1)
    return None


def main(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    for n, r in enumerate(rows[1:], start=1):
        provision, component, value, grade, source, last, nxt, pending, notes = r
        resolved = dt.date.fromisoformat(last)
        exp = expiry(nxt, resolved)
        if exp is None:
            print(f"row {n}: no date in next check {nxt!r}; expires_on left null", file=sys.stderr)
        a = {
            "id": f"{last}-{n:02d}",
            "subject": provision,
            "component": component,
            "value": value,
            "grade": grade,
            "recorded_on": last,
            "source": source,
            "expires_on": exp.isoformat() if exp else None,
            "next_check": nxt,
            "pending_changes": pending,
            "supersedes": None,
            "note": notes,
        }
        print(json.dumps(a, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
