#!/usr/bin/env python3
"""catchlog — read a catch log and say, for each component, what kind of zero it has.

A log that counts only corrections cannot tell a component that was checked and
found sound from a component that was never checked: both show zero. The
difference is the confirmations. This tool counts corrections and confirmations
apart, for each component and for each phase (before and after release), and
names each cell:

    found        at least one correction
    clean        no correction, and at least one confirmation
    other-only   no correction and no confirmation, but other rows (an
                 abstention, a rule sharpened): something was looked at, and
                 the log does not say it was sound
    unexamined   no row at all: zero means nothing here

It never adds corrections and confirmations together, and gives no rate.

Outcomes (the workbook's list, kit v1.0):
    corrections    corrected, deleted, weakened, excluded, slipped
    confirmations  confirmed, "confirmed (no error found)"
    other          abstained, and anything else (e.g. "rule sharpened")

Input: CSV with the columns
    no         the entry's number, or a label for a row that is not a numbered entry
    component  one or more component names, joined by + ＋ → , / or ／; English
               or Japanese names from csv/components.csv, or "outside" (対象外)
    outcome    as above
    phase      pre, post, pre-release, post-release, 公開前 or 公開後
and optionally
    count      how many checks or corrections the row stands for: a whole number
               (default 1), or "uncounted" on a confirmation row, meaning
               "confirmations were recorded but not counted" (the cell is clean,
               and its count is shown as "uncounted")

It also reads the workbook's Catch log sheet saved as CSV: the bilingual headers
("Component(s)" + newline + "成分", or the template's "Component(s) / 成分"), the
title rows above them, the grey "Ex." row (skipped) and the numbered empty rows
(skipped). A file that is not UTF-8 is read as cp932 (Japanese Excel's default).

With --fields it reports, instead, how full each column is: for every column,
how many rows have it filled, how many mark it as not yet decided (or not recorded), and how many
leave it blank, before and after release, and which entries have no decision in
"what would have happened" and "stakes". It fills nothing in. A value counts as
"not yet decided" when it is only a dash (— – ― － -), a dash followed by a note in
brackets ("—（未判断、2026-10-20）"), or only one of 未判断, 著者が記入, 記録なし,
"not yet decided", "to be decided", "not recorded", "TBD", "N/A" or "?" (in brackets or
not), alone or followed by a note in brackets ("記録なし（2026-10-20には…）", kit v1.13).
Anything else is an answer, even if it mentions those words. A row whose phase is
blank or unknown is counted under "unknown" rather than stopping the report. If the log has the
column "Who wrote 'what would have happened'?" (kit v1.8), its values are counted.

Usage:
    python3 catchlog.py LOG.csv [--components csv/components.csv] [--strict] [--json]
    python3 catchlog.py LOG.csv --fields [--json]

An unknown component name is reported on stderr; with --strict it is an error.
Exit status: 0, or 2 on unreadable input.

Standard library only. CC0 1.0. Part of the citation provenance kit (v1.8).
"""
import argparse
import csv
import io
import json
import os
import re
import sys

CORRECTIONS = {"corrected", "deleted", "weakened", "excluded", "slipped"}
CONFIRMATIONS = {"confirmed", "confirmed (no error found)"}
PHASE_NAMES = {"pre": "pre", "pre-release": "pre", "公開前": "pre",
               "post": "post", "post-release": "post", "公開後": "post"}
PHASES = ("pre", "post")
HEADERS = {
    "no": {"no", "#"},
    "component": {"component", "component(s)", "components", "成分"},
    "outcome": {"outcome", "結果"},
    "phase": {"phase", "公開前／後", "公開前/後"},
    "count": {"count", "件数"},
}
OUTSIDE = {"outside", "対象外"}
SPLIT = re.compile(r"\s*(?:\+|＋|→|->|,|、|/|／)\s*")
HERE = os.path.dirname(os.path.abspath(__file__))


def load_components(path=None):
    """Return {name as written (casefolded), English or Japanese: English name}, in order."""
    path = path or os.path.join(HERE, "..", "csv", "components.csv")
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    names = {}
    for r in rows[1:]:
        if r and r[0].strip():
            en = r[0].strip()
            names[en.casefold()] = en
            if len(r) > 1 and r[1].strip():
                names[r[1].strip().casefold()] = en
    if not names:
        raise ValueError(f"{path}: no components")
    return names


def _key(header):
    """Match a header cell, in any of its forms: one line, two lines, or "EN / JA"."""
    h = re.sub(r"\s+", " ", (header or "").replace("﻿", "")).strip().casefold()
    parts = {h} | {p.strip() for p in re.split(r"\n| / | ／ ", (header or "").replace("﻿", "").casefold())}
    for k, names in HEADERS.items():
        if parts & names:
            return k
    return None


def _decode(path):
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8-sig", "cp932"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"{path}: neither UTF-8 nor cp932; save it as CSV UTF-8")


def _count(v, kind, no):
    v = v.strip()
    if not v:
        return 1
    if v.casefold() == "uncounted":
        if kind != "confirmation":
            raise ValueError(f"entry {no!r}: only a confirmation can be uncounted")
        return None
    if not re.fullmatch(r"\d+", v):
        raise ValueError(f"entry {no!r}: count must be a whole number or 'uncounted', not {v!r}")
    n = int(v)
    if n == 0:
        raise ValueError(f"entry {no!r}: a count of 0 is not a row; leave the row out")
    return n


def _kind(outcome):
    o = (outcome or "").strip().casefold()
    if o in CORRECTIONS:
        return "correction"
    if o in CONFIRMATIONS:
        return "confirmation"
    return "other"


class LogRows(list):
    """The rows of a log, with the column labels in order and the labels of no and phase."""
    labels = ()
    skip = ()


def read_log(path, components=None, strict=False, warn=None, columns_only=False):
    """Read a catch log. With columns_only (for --fields), component and outcome are optional."""
    components = components or load_components()
    rows_in = list(csv.reader(io.StringIO(_decode(path))))
    if not rows_in:
        raise ValueError(f"{path}: empty file")
    cols, start = None, None
    for i, line in enumerate(rows_in[:10]):
        found = {}
        for j, h in enumerate(line):
            k = _key(h)
            if k:
                if k in found:
                    raise ValueError(f"{path}: two {k} columns")
                found[k] = j
        if ({"no", "phase"} if columns_only else {"component", "outcome"}) <= set(found):
            cols, start, header = found, i + 1, line
            break
    if cols is None:
        need = "no and phase" if columns_only else "component and outcome"
        raise ValueError(f"{path}: no header row with {need} columns in the first 10 rows")
    missing = [k for k in (("no", "phase") if columns_only else ("no", "component", "outcome", "phase")) if k not in cols]
    if missing:
        raise ValueError(f"missing column(s): {', '.join(missing)}")
    labels = [_label(h) if h.strip() else "" for h in header]
    seen = set()
    for lab in labels:
        if lab and lab in seen:
            raise ValueError(f"{path}: two columns named {lab!r}")
        seen.add(lab)
    rows, unknown = LogRows(), []
    rows.labels = tuple(lab for lab in labels if lab)
    rows.skip = (labels[cols["no"]], labels[cols["phase"]])
    for line in rows_in[start:]:
        get = lambda k: line[cols[k]].strip() if k in cols and cols[k] < len(line) else ""
        no = get("no")
        rest = [c for j, c in enumerate(line) if j != cols["no"] and c.strip()]
        if not rest or no.casefold().rstrip(".") == "ex":
            continue                      # an unused numbered row, or the template's example
        comps = []
        for c in (c for c in SPLIT.split(get("component")) if c.strip()):
            cf = c.casefold()
            if cf in OUTSIDE:
                comps.append("outside")
            elif cf in components:
                comps.append(components[cf])
            else:
                comps.append(c)
                unknown.append((no, c))
        if not comps and not columns_only:
            raise ValueError(f"entry {no!r}: no component")
        ph = re.sub(r"\s*[（(].*$", "", get("phase")).casefold()
        if ph not in PHASE_NAMES and columns_only:
            phase = "unknown"
        elif ph not in PHASE_NAMES:
            raise ValueError(f"entry {no!r}: phase must be pre or post (or 公開前／公開後), not {get('phase')!r}")
        else:
            phase = PHASE_NAMES[ph]
        kind = _kind(get("outcome"))
        rows.append({"no": no, "components": comps, "outcome": get("outcome"), "kind": kind,
                     "phase": phase, "count": _count(get("count"), kind, no) if not columns_only else 1,
                     "fields": {labels[j]: (line[j].strip() if j < len(line) else "")
                                for j in range(len(header)) if labels[j]}})
    if unknown:
        msg = "; ".join(f"entry {n!r}: {c!r}" for n, c in unknown)
        if strict:
            raise ValueError(f"unknown component(s): {msg}")
        (warn or (lambda m: print(m, file=sys.stderr)))(f"catchlog: unknown component(s), counted as written: {msg}")
    return rows


def _label(h):
    """A column's display name: its first line (the workbook writes "English\nJapanese")."""
    return re.split(r"\n| / | ／ |／", h.replace("\ufeff", "").strip())[0].strip()


_DASH = "—–―－-"
_NOTE = r"(?:\s*[（(][^（()）]*[)）])?"  # one note in brackets, not nested, at the end
PENDING = re.compile(r"[%s]+" % _DASH + _NOTE + r"|[（(]?\s*(?:未判断|著者が記入|記録なし|not yet decided|to be decided|"
                     r"not recorded|tbd|n/?a|\?)\s*[)）]?\.?" + _NOTE, re.I)
WOULD = re.compile(r"^what would have happened|^見逃していたら何が", re.I)
STAKES_COL = re.compile(r"^stakes\b|影響の大きさ", re.I)
WHO_COL = re.compile(r"^who wrote|誰が書いたか", re.I)
FIELD_PHASES = ("pre", "post", "unknown")


def state(value):
    """'blank', 'pending' (not yet decided or not recorded) or 'filled'."""
    v = (value or "").strip()
    return "blank" if not v else "pending" if PENDING.fullmatch(v) else "filled"


def fields(rows):
    """{column: {phase: {"filled": n, "pending": n, "blank": n}}} for every column except the
    entry number and the phase, the entries with no decision (blank or pending) in the two
    judgment columns, and the counts of the 'who wrote' column."""
    labels = getattr(rows, "labels", None) or list(dict.fromkeys(k for r in rows for k in r["fields"]))
    skip = getattr(rows, "skip", ())
    cols = [c for c in labels if c not in skip]
    out = {c: {p: {"filled": 0, "pending": 0, "blank": 0} for p in FIELD_PHASES} for c in cols}
    undecided = {}
    who = {}
    for r in rows:
        for c in cols:
            v = r["fields"].get(c, "")
            st = state(v)
            out[c][r["phase"]][st] += 1
            if st != "filled" and (WOULD.search(c) or STAKES_COL.search(c)):
                undecided.setdefault(c, []).append(r["no"])
            if WHO_COL.search(c):
                who[v or "(blank)"] = who.get(v or "(blank)", 0) + 1
    return {"columns": out, "undecided": undecided, "who": who}


def tally(rows, components=None):
    """{component: {phase: {"corrections": int, "confirmations": int, "uncounted": bool,
    "other": int, "status": found|clean|other-only|unexamined, "entries": {kind: [no, ...]}}}}"""
    components = components or load_components()
    order = list(dict.fromkeys(components.values()))
    names = order + sorted({c for r in rows for c in r["components"]} - set(order))
    out = {c: {p: {"corrections": 0, "confirmations": 0, "uncounted": False, "other": 0,
                   "entries": {"correction": [], "confirmation": [], "other": []}}
               for p in PHASES} for c in names}
    for r in rows:
        for c in r["components"]:
            cell = out[c][r["phase"]]
            if r["count"] is None:
                cell["uncounted"] = True
            elif r["kind"] == "correction":
                cell["corrections"] += r["count"]
            elif r["kind"] == "confirmation":
                cell["confirmations"] += r["count"]
            else:
                cell["other"] += r["count"]
            cell["entries"][r["kind"]].append(r["no"])
    for c in out:
        for p in PHASES:
            cell = out[c][p]
            if cell["corrections"]:
                cell["status"] = "found"
            elif cell["confirmations"] or cell["uncounted"]:
                cell["status"] = "clean"
            elif cell["other"]:
                cell["status"] = "other-only"
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
    ap.add_argument("--strict", action="store_true", help="an unknown component name is an error")
    ap.add_argument("--fields", action="store_true", help="report how full each column is instead")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        comps = load_components(a.components)
        rows = read_log(a.log, comps, strict=a.strict, columns_only=a.fields)
    except (OSError, ValueError, csv.Error) as e:
        print(f"catchlog: {e}", file=sys.stderr)
        return 2
    if a.fields:
        f = fields(rows)
        if a.json:
            print(json.dumps({"rows": len(rows), **f}, ensure_ascii=False, indent=1))
            return 0
        print(f"{len(rows)} row(s). filled / not yet decided / blank, before and after release")
        w = max([len(c) for c in f["columns"]] + [6])
        shown = [p for p in FIELD_PHASES if p != "unknown" or any(r["phase"] == "unknown" for r in rows)]
        for c, cells in f["columns"].items():
            parts = [f"{p} {cells[p]['filled']} / {cells[p]['pending']} / {cells[p]['blank']}" for p in shown]
            print(f"{c[:w]:<{w}}  " + "    ".join(f"{x:<16}" for x in parts).rstrip())
        for c, nos in f["undecided"].items():
            print(f"no decision in '{c}': " + ", ".join(nos))
        if f["who"]:
            print("who wrote 'what would have happened': " + "; ".join(f"{k} {v}" for k, v in f["who"].items()))
        return 0
    t = tally(rows, comps)
    if a.json:
        print(json.dumps({"rows": len(rows), "components": t}, ensure_ascii=False, indent=1))
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
