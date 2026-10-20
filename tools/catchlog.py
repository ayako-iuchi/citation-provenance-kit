#!/usr/bin/env python3
"""catchlog — read a catch log and say, for each component, what kind of zero it has.

A log that counts only corrections cannot tell a component that was checked and
found sound from a component that was never checked: both show zero. The
difference is the confirmations. This tool counts corrections and confirmations
apart, for each component and for each phase (before and after release), and
names each cell:

    found        at least one correction
    clean        no correction, and at least one confirmation
    unexamined   no correction and no confirmation: zero means nothing here

It never adds corrections and confirmations together, and gives no rate.

Outcomes (the workbook's list, kit v1.0):
    corrections    corrected, deleted, weakened, excluded, slipped
    confirmations  confirmed, "confirmed (no error found)"
    other          abstained, and anything else (e.g. "rule sharpened"),
                   counted and listed but in neither of the two

Input: CSV with at least the columns
    no         the entry's number (or a label for an uncounted row, e.g. "A-3")
    component  one or more component names joined by "+" or "→"
               ("outside" for an entry outside the provenance components)
    outcome    as above
    phase      "pre" or "post" (before or after release)
and optionally
    count      a whole number, or empty. Empty on a confirmation row means
               "confirmations were recorded but not counted": the cell is clean,
               and its count is shown as "uncounted".
The workbook's own headers ("Component(s) / 成分", "Outcome / 結果",
"Phase / 公開前／後", "Pre-release"/"Post-release") are also read.

Usage:
    python3 catchlog.py LOG.csv [--components csv/components.csv] [--json]

Standard library only. CC0 1.0. Part of the citation provenance kit (v1.7).
"""
import argparse
import csv
import json
import os
import re
import sys

CORRECTIONS = {"corrected", "deleted", "weakened", "excluded", "slipped"}
CONFIRMATIONS = {"confirmed", "confirmed (no error found)"}
PHASES = ("pre", "post")
HEADERS = {
    "no": ("no", "#"),
    "component": ("component", "component(s) / 成分", "component(s)"),
    "outcome": ("outcome", "outcome / 結果"),
    "phase": ("phase", "phase / 公開前／後"),
    "count": ("count",),
}
HERE = os.path.dirname(os.path.abspath(__file__))


def load_components(path=None):
    path = path or os.path.join(HERE, "..", "csv", "components.csv")
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    names = [r[0].strip() for r in rows[1:] if r and r[0].strip()]
    return names


def _key(header):
    h = header.strip().lstrip("﻿").casefold()
    for k, names in HEADERS.items():
        if h in names:
            return k
    return None


def _phase(v):
    v = (v or "").strip().casefold()
    if v.startswith("pre"):
        return "pre"
    if v.startswith("post"):
        return "post"
    raise ValueError(f"phase must be pre or post, not {v!r}")


def _kind(outcome):
    o = (outcome or "").strip().casefold()
    if o in CORRECTIONS:
        return "correction"
    if o in CONFIRMATIONS:
        return "confirmation"
    return "other"


def read_log(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        cols = {}
        for i, h in enumerate(header):
            k = _key(h)
            if k and k not in cols:
                cols[k] = i
        missing = [k for k in ("no", "component", "outcome", "phase") if k not in cols]
        if missing:
            raise ValueError(f"missing column(s): {', '.join(missing)}")
        rows = []
        for line in reader:
            if not any(c.strip() for c in line):
                continue
            get = lambda k: line[cols[k]].strip() if k in cols and cols[k] < len(line) else ""
            comps = [c.strip() for c in re.split(r"\s*(?:\+|→|->)\s*", get("component")) if c.strip()]
            if not comps:
                raise ValueError(f"entry {get('no')!r}: no component")
            cnt = get("count")
            rows.append({"no": get("no"), "components": comps, "outcome": get("outcome"),
                         "kind": _kind(get("outcome")), "phase": _phase(get("phase")),
                         "count": int(cnt) if cnt else None})
    return rows


def tally(rows, components):
    """{component: {phase: {"corrections": n, "confirmations": n or "uncounted"/"n+",
    "other": n, "status": found|clean|unexamined, "entries": {...}}}}"""
    names = list(components) + sorted({c for r in rows for c in r["components"]} - set(components))
    out = {c: {p: {"corrections": 0, "confirmations": 0, "uncounted": False, "other": 0,
                   "entries": {"correction": [], "confirmation": [], "other": []}}
               for p in PHASES} for c in names}
    for r in rows:
        n = r["count"] if r["count"] is not None else 1
        for c in r["components"]:
            cell = out[c][r["phase"]]
            if r["kind"] == "correction":
                cell["corrections"] += n
            elif r["kind"] == "confirmation":
                if r["count"] is None and not re.fullmatch(r"#?\d+", r["no"]):
                    cell["uncounted"] = True
                else:
                    cell["confirmations"] += n
            else:
                cell["other"] += n
            cell["entries"][r["kind"]].append(r["no"])
    for c in out:
        for p in PHASES:
            cell = out[c][p]
            if cell["corrections"]:
                cell["status"] = "found"
            elif cell["confirmations"] or cell["uncounted"]:
                cell["status"] = "clean"
            else:
                cell["status"] = "unexamined"
    return out


def _conf(cell):
    if cell["uncounted"]:
        return f"{cell['confirmations']}+uncounted" if cell["confirmations"] else "uncounted"
    return str(cell["confirmations"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("log")
    ap.add_argument("--components", help="components.csv (default: the kit's)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        comps = load_components(a.components)
        rows = read_log(a.log)
    except (OSError, UnicodeDecodeError, ValueError, csv.Error, StopIteration) as e:
        print(f"catchlog: {e}", file=sys.stderr)
        return 2
    t = tally(rows, comps)
    if a.json:
        print(json.dumps({"entries": len(rows), "components": t}, ensure_ascii=False, indent=1))
        return 0
    print(f"{len(rows)} row(s). corrections / confirmations / status, before and after release")
    print(f"{'component':<14} {'pre':<34} post")
    for c, cells in t.items():
        parts = []
        for p in PHASES:
            cell = cells[p]
            s = f"{cell['corrections']} / {_conf(cell)} / {cell['status']}"
            if cell["other"]:
                s += f" (+{cell['other']} other)"
            parts.append(s)
        print(f"{c:<14} {parts[0]:<34} {parts[1]}")
    un = [c for c in t if t[c]["pre"]["status"] == "unexamined" and c != "outside"]
    if un:
        print("unexamined before release (zero means nothing): " + ", ".join(un))
    return 0


if __name__ == "__main__":
    sys.exit(main())
