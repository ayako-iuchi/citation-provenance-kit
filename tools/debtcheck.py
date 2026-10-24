#!/usr/bin/env python3
"""debtcheck — count the fixes that were found and put off, and how long they have waited.

The method paper's §8-4 says the cost of the discipline "arrives in lumps, late,
when a rule fires on work already believed finished". A fix that is found and put
off to "the next edition" is such a lump, waiting. Nothing in a catch log adds
them up: each entry says "to be fixed in the next edition", and the entries are
read one at a time.

This tool reads an append-only register of four kinds of line
(schema/deferred.schema.json):

    deferral    a fix found and put off: the log entry, the document, the place,
                when it is to be made ("next edition", "next revision", or a named
                edition such as "v1.3"), any condition, the date found and the
                date recorded
    payment     the fix being made: which deferral, the day the edition carrying
                it was published, and that edition
    withdrawal  a deferral closed without a fix: its condition was not met, or it
                was decided not to make it; with the reason
    edition     an edition of a document being published

and reports, for each document, as of a day:

    open       deferrals with no payment or withdrawal (conditional ones counted
               apart)
    paid       deferrals with a payment; withdrawn, those with a withdrawal
    oldest     the open deferral found longest ago, and its age in days; when the
               log does not record the date found, the date recorded is used and
               the report says so
    overdue    an open deferral whose edition has come out without it. For "next
               edition" or "next revision": an edition of the same document
               published on a later day than the deferral was recorded (an
               edition published the same day is taken to be the one the fix was
               found in). For a named edition: that edition has been published,
               whenever that was. A conditional deferral that is overdue is
               marked as conditional.

"As of a day" reads the dates the lines carry: a deferral counts from the day it
was recorded, a payment or withdrawal from its day, an edition from the day it
was published. A document is listed when a line about it is dated on or before
that day. An edition whose date is not recorded is listed as undated and never
makes anything overdue. A line appended later about an earlier day changes the
report for that day: the register records what happened, and when it was learnt is
in its history.

It counts and dates. It says nothing about how long a fix will take, and does not
say how to fix anything.

Usage:
    python3 debtcheck.py REGISTER --on YYYY-MM-DD [--list] [--json]
    python3 debtcheck.py REGISTER --check

Exit status: 0; 1 if anything is overdue (or, with --check, the register has
problems); 2 on unreadable or malformed input.

Standard library only. CC0 1.0. Part of the citation provenance kit (v1.13).
"""
import argparse
import datetime as dt
import json
import re
import sys

FIELDS = {
    "deferral": {"id", "kind", "log", "document", "where", "fix_in", "condition", "found_on", "recorded_on", "decided_by", "note"},
    "payment": {"id", "kind", "pays", "paid_on", "paid_in", "note"},
    "withdrawal": {"id", "kind", "withdraws", "withdrawn_on", "reason", "note"},
    "edition": {"id", "kind", "document", "edition", "published_on", "note"},
}
DATES = {"deferral": ("found_on", "recorded_on"), "payment": ("paid_on",), "withdrawal": ("withdrawn_on",),
         "edition": ("published_on",)}
NULLABLE = {"found_on", "published_on", "condition"}
NEXT = ("next edition", "next revision")
NEXT_LIKE = re.compile(r"^\s*(?:the\s+)?next\s+(?:edition|revision|version|release)\s*$|^\s*次の(?:版|改訂)\s*$", re.I)
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class Malformed(ValueError):
    pass


def _day(s, where):
    if not isinstance(s, str) or not DAY.match(s):
        raise Malformed(f"{where}: a date must be written YYYY-MM-DD, not {s!r}")
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        raise Malformed(f"{where}: {s!r} is not a date") from None


def _no_duplicates(pairs):
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise Malformed(f"key {k!r} appears twice")
        seen[k] = v
    return seen


def load(path):
    """Read and validate the register's shape. Raises Malformed."""
    try:
        with open(path, encoding="utf-8-sig") as f:
            lines = [(n, line) for n, line in enumerate(f, start=1) if line.strip()]
    except (OSError, UnicodeDecodeError) as e:
        raise Malformed(f"{path}: {e}") from None
    recs = []
    for n, line in lines:
        where = f"line {n}"
        try:
            r = json.loads(line, object_pairs_hook=_no_duplicates)
        except Malformed as e:
            raise Malformed(f"{where}: {e}") from None
        except (ValueError, RecursionError) as e:
            raise Malformed(f"{where}: not JSON ({e.__class__.__name__})") from None
        if not isinstance(r, dict):
            raise Malformed(f"{where}: a line must be a JSON object")
        kind = r.get("kind")
        if kind not in FIELDS:
            raise Malformed(f"{where}: kind must be deferral, payment, withdrawal or edition, not {kind!r}")
        keys = set(r)
        if keys != FIELDS[kind]:
            missing, extra = sorted(FIELDS[kind] - keys), sorted(keys - FIELDS[kind])
            raise Malformed(f"{where}: {kind} " + "; ".join(x for x in (
                missing and "missing " + ", ".join(missing), extra and "unknown " + ", ".join(extra)) if x))
        for k, v in r.items():
            if v is None and k in NULLABLE:
                continue
            if not isinstance(v, str):
                raise Malformed(f"{where}: {k} must be text")
        for k in DATES[kind]:
            if r[k] is not None:
                _day(r[k], f"{where}: {k}")
        r["_line"] = n
        recs.append(r)
    return recs


def check(recs):
    """Problems with the register as a whole (empty list if none)."""
    problems, ids, deferrals, closed, editions = [], set(), {}, {}, {}
    for r in recs:
        if r["kind"] == "edition":
            key = (r["document"], r["edition"])
            if key in editions:
                problems.append(f"line {r['_line']}: edition {r['edition']} of {r['document']} is recorded twice (line {editions[key]})")
            editions.setdefault(key, r["_line"])
    for r in recs:
        n = r["_line"]
        if r["id"] in ids:
            problems.append(f"line {n}: id {r['id']} is used twice")
        ids.add(r["id"])
        if r["kind"] == "deferral":
            deferrals[r["id"]] = r
            if r["found_on"] and r["found_on"] > r["recorded_on"]:
                problems.append(f"line {n}: found on {r['found_on']}, after it was recorded ({r['recorded_on']})")
            if r["fix_in"] not in NEXT and NEXT_LIKE.match(r["fix_in"]):
                problems.append(f"line {n}: fix_in {r['fix_in']!r}: write 'next edition' or 'next revision' exactly, or name an edition")
            elif r["fix_in"] != r["fix_in"].strip() or not r["fix_in"]:
                problems.append(f"line {n}: fix_in {r['fix_in']!r} has spaces at its ends or is empty")
        elif r["kind"] in ("payment", "withdrawal"):
            target = r["pays"] if r["kind"] == "payment" else r["withdraws"]
            day = r["paid_on"] if r["kind"] == "payment" else r["withdrawn_on"]
            d = deferrals.get(target)
            if d is None:
                problems.append(f"line {n}: {r['kind']} of {target}, which is not a deferral recorded earlier")
                continue
            if target in closed:
                problems.append(f"line {n}: {target} is already closed (line {closed[target]})")
            closed[target] = n
            if day < d["recorded_on"]:
                problems.append(f"line {n}: dated {day}, before the deferral was recorded ({d['recorded_on']})")
            if r["kind"] == "payment" and (d["document"], r["paid_in"]) not in editions:
                problems.append(f"line {n}: paid in {r['paid_in']}, which is not an edition of {d['document']} in the register")
    return problems


def report(recs, on):
    """{document: {...}} as of `on` (a date)."""
    on = on if isinstance(on, dt.date) else _day(on, "--on")
    iso = on.isoformat()
    deferrals = [r for r in recs if r["kind"] == "deferral" and r["recorded_on"] <= iso]
    closes = {}
    for r in recs:
        if r["kind"] == "payment" and r["paid_on"] <= iso:
            closes[r["pays"]] = "paid"
        elif r["kind"] == "withdrawal" and r["withdrawn_on"] <= iso:
            closes[r["withdraws"]] = "withdrawn"
    editions = [r for r in recs if r["kind"] == "edition" and r["published_on"] and r["published_on"] <= iso]
    present = [r["document"] for r in deferrals] + [r["document"] for r in editions] + [
        r["document"] for r in recs if r["kind"] == "edition" and not r["published_on"]]
    docs = [d for d in dict.fromkeys(r["document"] for r in recs if r["kind"] in ("deferral", "edition")) if d in present]
    out = {}
    for doc in docs:
        mine = [d for d in deferrals if d["document"] == doc]
        eds = sorted((e for e in editions if e["document"] == doc), key=lambda e: (e["published_on"], e["_line"]))
        undated = [e["edition"] for e in recs if e["kind"] == "edition" and e["document"] == doc and not e["published_on"]]
        open_, paid_, withdrawn_, overdue = [], [], [], []
        for d in mine:
            state = closes.get(d["id"])
            if state == "paid":
                paid_.append(d)
                continue
            if state == "withdrawn":
                withdrawn_.append(d)
                continue
            open_.append(d)
            if d["fix_in"] in NEXT:
                later = [e for e in eds if e["published_on"] > d["recorded_on"]]
                if later:
                    overdue.append((d, later[0]))
            else:
                named = [e for e in eds if e["edition"] == d["fix_in"]]
                if named:
                    overdue.append((d, named[0]))

        def basis(d):
            return (d["found_on"], "found") if d["found_on"] else (d["recorded_on"], "recorded")
        oldest = None
        if open_:
            d = min(open_, key=lambda d: (basis(d)[0], d["_line"]))
            day, how = basis(d)
            oldest = {"id": d["id"], "log": d["log"], "date": day, "basis": how, "age_days": (on - dt.date.fromisoformat(day)).days}
        out[doc] = {
            "open": len(open_),
            "conditional": sum(1 for d in open_ if d["condition"]),
            "paid": len(paid_),
            "withdrawn": len(withdrawn_),
            "found_date_not_recorded": [d["log"] for d in open_ if not d["found_on"]],
            "oldest": oldest,
            "latest_edition": ({"edition": eds[-1]["edition"], "published_on": eds[-1]["published_on"]} if eds else None),
            "undated_editions": undated,
            "overdue": [{"id": d["id"], "log": d["log"], "fix_in": d["fix_in"], "condition": d["condition"],
                         "edition": e["edition"], "published_on": e["published_on"]} for d, e in overdue],
            "open_items": [{"id": d["id"], "log": d["log"], "where": d["where"], "fix_in": d["fix_in"], "condition": d["condition"],
                            "found_on": d["found_on"], "recorded_on": d["recorded_on"], "decided_by": d["decided_by"]} for d in open_],
        }
    return out


def render(rep, on, show_list=False):
    lines = [f"Deferred fixes as of {on}. Counts and dates only: nothing here says how long a fix will take."]
    for doc, r in rep.items():
        ed = r["latest_edition"]
        if ed:
            edtext = f"latest edition {ed['edition']} ({ed['published_on']})"
        elif r["undated_editions"]:
            edtext = f"edition {', '.join(r['undated_editions'])} (date not recorded)"
        else:
            edtext = "no edition recorded"
        cond = f" ({r['conditional']} conditional)" if r["conditional"] else ""
        wd = f", withdrawn {r['withdrawn']}" if r["withdrawn"] else ""
        lines.append("")
        lines.append(f"{doc}")
        lines.append(f"  open {r['open']}{cond}, paid {r['paid']}{wd}; {edtext}")
        o = r["oldest"]
        if o:
            lines.append(f"  oldest open: {o['log']}, {o['basis']} {o['date']}, {o['age_days']} days")
        if r["found_date_not_recorded"]:
            lines.append(f"  date found not recorded: {', '.join(r['found_date_not_recorded'])}")
        for x in r["overdue"]:
            c = f" (conditional: {x['condition']})" if x["condition"] else ""
            lines.append(f"  OVERDUE {x['log']}: to be fixed in {x['fix_in']}; {x['edition']} came out on {x['published_on']} without it{c}")
        if show_list:
            for i in r["open_items"]:
                c = f" [{i['condition']}]" if i["condition"] else ""
                lines.append(f"    {i['log']}: {i['where']} — {i['fix_in']}{c}")
    total_open = sum(r["open"] for r in rep.values())
    total_over = sum(len(r["overdue"]) for r in rep.values())
    lines.append("")
    lines.append(f"open {total_open}, overdue {total_over}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("register")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--on", help="the day to report as of (YYYY-MM-DD)")
    g.add_argument("--check", action="store_true", help="check the register as a whole")
    ap.add_argument("--list", action="store_true", help="list the open deferrals")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        recs = load(a.register)
        on = _day(a.on, "--on") if a.on else None
    except Malformed as e:
        print(f"debtcheck: {e}", file=sys.stderr)
        return 2
    problems = check(recs)
    if a.check:
        for p in problems:
            print(p)
        if not problems:
            print(f"{len(recs)} line(s); no problems")
        return 1 if problems else 0
    if problems:
        for p in problems:
            print(f"debtcheck: {p}", file=sys.stderr)
        return 2
    rep = report(recs, on)
    if a.json:
        print(json.dumps({"on": on.isoformat(), "documents": rep}, ensure_ascii=False, indent=2))
    else:
        print(render(rep, on.isoformat(), a.list))
    return 1 if any(r["overdue"] for r in rep.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
