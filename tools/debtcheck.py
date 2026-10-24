#!/usr/bin/env python3
"""debtcheck — count the fixes that were found and put off, and how long they have waited.

The method paper's §8-4 says the cost of the discipline "arrives in lumps, late,
when a rule fires on work already believed finished". A fix that is found and put
off to "the next edition" is such a lump, waiting. Nothing in a catch log adds
them up: each entry says "to be fixed in the next edition", and the entries are
read one at a time.

This tool reads an append-only register of three kinds of line
(schema/deferred.schema.json):

    deferral   a fix found and put off: the log entry, the document, the place,
               when it is to be made ("next edition", or a named edition),
               any condition, the date found and the date recorded
    payment    the fix being made: which deferral, when, in which edition
    edition    an edition of a document being published

and reports, for each document, as of a day:

    open       deferrals with no payment (conditional ones counted apart)
    paid       deferrals with a payment
    oldest     the open deferral found longest ago, and its age in days; when the
               log does not record the date found, the date recorded is used and
               the report says so
    overdue    an open deferral whose edition has come out without it: "next
               edition" (or "next revision") with an edition of the same document
               published after the deferral was recorded, or a named edition
               that has been published

It counts and dates. It says nothing about how long a fix will take, and does not
say how to fix anything. Lines dated after the day asked about are ignored, so the
register can be read as it stood on an earlier day.

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
import sys

FIELDS = {
    "deferral": {"id", "kind", "log", "document", "where", "fix_in", "condition", "found_on", "recorded_on", "decided_by", "note"},
    "payment": {"id", "kind", "pays", "paid_on", "paid_in", "note"},
    "edition": {"id", "kind", "document", "edition", "published_on", "note"},
}
DATES = {"deferral": ("found_on", "recorded_on"), "payment": ("paid_on",), "edition": ("published_on",)}
NULLABLE = {"found_on", "published_on", "condition"}
NEXT = ("next edition", "next revision")


class Malformed(ValueError):
    pass


def _day(s, where):
    if not isinstance(s, str) or len(s) != 10:
        raise Malformed(f"{where}: a date must be written YYYY-MM-DD, not {s!r}")
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        raise Malformed(f"{where}: {s!r} is not a date") from None


def load(path):
    """Read and validate the register's shape. Raises Malformed."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = [(n, line) for n, line in enumerate(f, start=1) if line.strip()]
    except (OSError, UnicodeDecodeError) as e:
        raise Malformed(f"{path}: {e}") from None
    recs = []
    for n, line in lines:
        where = f"line {n}"
        try:
            r = json.loads(line)
        except (json.JSONDecodeError, RecursionError) as e:
            raise Malformed(f"{where}: not JSON ({e.__class__.__name__})") from None
        if not isinstance(r, dict):
            raise Malformed(f"{where}: a line must be a JSON object")
        kind = r.get("kind")
        if kind not in FIELDS:
            raise Malformed(f"{where}: kind must be deferral, payment or edition, not {kind!r}")
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
    problems, ids, deferrals, paid = [], set(), {}, {}
    for r in recs:
        n = r["_line"]
        if r["id"] in ids:
            problems.append(f"line {n}: id {r['id']} is used twice")
        ids.add(r["id"])
        if r["kind"] == "deferral":
            deferrals[r["id"]] = r
            if r["found_on"] and r["found_on"] > r["recorded_on"]:
                problems.append(f"line {n}: found on {r['found_on']}, after it was recorded ({r['recorded_on']})")
        elif r["kind"] == "payment":
            d = deferrals.get(r["pays"])
            if d is None:
                problems.append(f"line {n}: pays {r['pays']}, which is not a deferral recorded earlier")
                continue
            if r["pays"] in paid:
                problems.append(f"line {n}: {r['pays']} is already paid (line {paid[r['pays']]})")
            paid[r["pays"]] = n
            if r["paid_on"] < d["recorded_on"]:
                problems.append(f"line {n}: paid on {r['paid_on']}, before the deferral was recorded ({d['recorded_on']})")
    return problems


def report(recs, on):
    """{document: {...}} as of `on` (a date)."""
    on = on if isinstance(on, dt.date) else _day(on, "--on")
    iso = on.isoformat()
    deferrals = [r for r in recs if r["kind"] == "deferral" and r["recorded_on"] <= iso]
    payments = {r["pays"]: r for r in recs if r["kind"] == "payment" and r["paid_on"] <= iso}
    editions = [r for r in recs if r["kind"] == "edition" and r["published_on"] and r["published_on"] <= iso]
    docs = list(dict.fromkeys([r["document"] for r in recs if r["kind"] in ("deferral", "edition")]))
    out = {}
    for doc in docs:
        mine = [d for d in deferrals if d["document"] == doc]
        eds = sorted((e for e in editions if e["document"] == doc), key=lambda e: e["published_on"])
        undated = [e["edition"] for e in recs if e["kind"] == "edition" and e["document"] == doc and not e["published_on"]]
        open_, paid_, overdue = [], [], []
        for d in mine:
            if d["id"] in payments:
                paid_.append(d)
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
            "found_date_not_recorded": [d["log"] for d in open_ if not d["found_on"]],
            "oldest": oldest,
            "latest_edition": ({"edition": eds[-1]["edition"], "published_on": eds[-1]["published_on"]} if eds else None),
            "undated_editions": undated,
            "overdue": [{"id": d["id"], "log": d["log"], "fix_in": d["fix_in"], "edition": e["edition"], "published_on": e["published_on"]} for d, e in overdue],
            "open_items": [{"id": d["id"], "log": d["log"], "where": d["where"], "fix_in": d["fix_in"], "condition": d["condition"],
                            "found_on": d["found_on"], "recorded_on": d["recorded_on"], "decided_by": d["decided_by"]} for d in open_],
        }
    return out


def render(rep, on, show_list=False):
    lines = [f"Deferred fixes as of {on}. Counts and dates only: nothing here says how long a fix will take."]
    for doc, r in rep.items():
        ed = r["latest_edition"]
        edtext = f"latest edition {ed['edition']} ({ed['published_on']})" if ed else (
            f"edition {', '.join(r['undated_editions'])} (date not recorded)" if r["undated_editions"] else "no edition recorded")
        cond = f" ({r['conditional']} conditional)" if r["conditional"] else ""
        lines.append("")
        lines.append(f"{doc}")
        lines.append(f"  open {r['open']}{cond}, paid {r['paid']}; {edtext}")
        o = r["oldest"]
        if o:
            lines.append(f"  oldest open: {o['log']}, {o['basis']} {o['date']}, {o['age_days']} days")
        if r["found_date_not_recorded"]:
            lines.append(f"  date found not recorded: {', '.join(r['found_date_not_recorded'])}")
        for x in r["overdue"]:
            lines.append(f"  OVERDUE {x['log']}: to be fixed in {x['fix_in']}; {x['edition']} came out on {x['published_on']} without it")
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
