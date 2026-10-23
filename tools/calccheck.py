#!/usr/bin/env python3
"""calccheck — computed values, and where each part of them came from.

A ratio, a month counted from a period, a count, a number of days: a value of
this kind has no source of its own. It has inputs, each with a source and a
grade; an operation; and someone who did the arithmetic. Written as a bare
number beside a grade, the value takes the grade of its inputs, and nothing in
the text says who computed it. Recomputing it checks the arithmetic, not where
the number came from.

register/computed.jsonl records, for each computed value: the value as shown,
verbatim, and where; its inputs (value, any range or alternative, the source,
the grade, and the status-log line the input depends on); the operation; how
it is shown (decimals, a month, a day); who did the arithmetic (source, author,
assistant, unknown), and what documents say about that; and the grade printed
beside it.

    python3 calccheck.py --log register/computed.jsonl \\
        --status register/status_log.jsonl --on 2026-10-23

Each record gets one verdict:
    recomputes       the operation on the recorded inputs gives the value shown
    differs          it gives another value
and these flags:
    grade-borrowed   someone other than the source did the arithmetic, and the
                     value is shown beside a grade A, with neither the grade nor
                     the value saying whose arithmetic it is (in the notation:
                     [figure: A | attribution: D], or words such as "author's
                     arithmetic"; only fixed forms are read)
    operator-unknown the record does not know who did the arithmetic
    claims-disagree  documents disagree about who did the arithmetic, or with
                     the record
    sensitive        an input's range or alternative changes the value as shown
                     (otherwise the value is robust to it)
    if-pending       a change recorded as pending would change the value as shown
    input-expired    the status-log line an input depends on has expired
    input-unrecorded the status log has no line for it
It is a report, not a gate: exit 1 whenever anything is flagged. It does not
say whether the operation is the right one for the argument (whether total
assets is the right denominator). That is a reading.

The operations are a closed list, evaluated without eval(): divide, add_months,
days_between, minutes_between, count. Dates are YYYY-MM-DD; times
YYYY-MM-DDTHH:MM.

Exit status: 0 nothing to report; 1 something reported; 2 a file could not be
read or a record is malformed. Standard library only. CC0 1.0. Part of the
citation provenance kit (kit v1.11).
"""
import argparse
import calendar
import datetime as dt
import itertools
import json
import os
import re
import sys
import unicodedata
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statuslog  # noqa: E402

OPERATORS = {"source", "author", "assistant", "unknown"}
OPS = {"divide": 2, "add_months": 2, "days_between": 2, "minutes_between": 2, "count": 2}
SHOWN_AS = {"percent", "decimal", "integer", "month", "day", "hours_minutes"}
RECORD_KEYS = {"id", "shown", "where", "inputs", "op", "display", "operator",
               "operator_claims", "grade_shown", "recorded_on", "recorded_by",
               "supersedes", "note"}
REQUIRED = {"id", "shown", "where", "inputs", "op", "display", "operator",
            "recorded_on", "recorded_by"}
INPUT_KEYS = {"name", "value", "unit", "range", "alternatives", "pending", "source",
              "grade", "status", "note"}
# Words that say the arithmetic is not the source's. A grade or a shown value
# that carries one of these counts as marked. Only fixed forms are read: a
# negation ("not computed") cannot be told from a mark by matching words.
MARKED = re.compile(
    r"attribution\s*:\s*D\b|帰属\s*:\s*D\b|author'?s\s+(?:own\s+)?(?:arithmetic|calculation)"
    r"|arithmetic\s*:\s*(?:author|assistant)|(?:derived|computed|calculated)\s+by\s+the\s+(?:author|assistant)"
    r"|著者の(?:計算|算出)|著者が(?:計算|算出)", re.I)
# A grade A as a token: after a bracket, a slot colon, a bar, a comma, or a
# space, and before a space, a bracket, a bar, punctuation, a dash or the end.
# grade_shown holds a grade, not prose, so "A text / B source" reads as A.
GRADE_A = re.compile(r"(?:(?<=^)|(?<=[\[(:|;,\s]))A(?=\s|$|[\])|;,.—–/-])")
NOT_GRADE = re.compile(r"(?:annex|appendix|exhibit|part|schedule|table|form|chapter)\s*$", re.I)
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")


def _norm(text):
    return unicodedata.normalize("NFKC", text or "")


def shows_a(grade):
    g = _norm(grade)
    for m in GRADE_A.finditer(g):
        if not NOT_GRADE.search(g[: m.start()]):
            return True
    return False


def marked(*texts):
    return any(MARKED.search(_norm(t)) for t in texts if t)


class Malformed(Exception):
    pass


def load(path):
    """Read the register (JSON Lines). Blank lines are ignored."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = [(n, l) for n, l in enumerate(f, start=1) if l.strip()]
    except (OSError, UnicodeDecodeError) as e:
        raise Malformed(f"{path}: {e}")
    out = []
    for n, line in lines:
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            raise Malformed(f"{path}, line {n}: not JSON ({e.msg})")
        if not isinstance(rec, dict):
            raise Malformed(f"{path}, line {n}: not an object")
        validate(rec, f"{path}, line {n}")
        out.append(rec)
    return out


def validate(rec, where):
    unknown = set(rec) - RECORD_KEYS
    if unknown:
        raise Malformed(f"{where}: unknown keys {sorted(unknown)}")
    missing = REQUIRED - set(rec)
    if missing:
        raise Malformed(f"{where}: missing {sorted(missing)}")
    if rec["operator"] not in OPERATORS:
        raise Malformed(f"{where}: operator must be one of {sorted(OPERATORS)}")
    op = rec["op"]
    if not isinstance(op, dict) or op.get("kind") not in OPS:
        raise Malformed(f"{where}: op.kind must be one of {sorted(OPS)}")
    if not isinstance(op.get("args"), list) or len(op["args"]) != OPS[op["kind"]]:
        raise Malformed(f"{where}: op {op['kind']} takes {OPS[op['kind']]} args")
    if not isinstance(rec["inputs"], list) or not rec["inputs"]:
        raise Malformed(f"{where}: inputs must be a non-empty list")
    names = set()
    for i in rec["inputs"]:
        if not isinstance(i, dict) or "name" not in i or "value" not in i:
            raise Malformed(f"{where}: each input needs name and value")
        bad = set(i) - INPUT_KEYS
        if bad:
            raise Malformed(f"{where}: input {i['name']}: unknown keys {sorted(bad)}")
        if i["name"] in names:
            raise Malformed(f"{where}: input {i['name']} twice")
        names.add(i["name"])
        if "range" in i and (not isinstance(i["range"], list) or len(i["range"]) != 2):
            raise Malformed(f"{where}: input {i['name']}: range is [low, high]")
        if "status" in i and not (isinstance(i["status"], dict)
                                  and {"subject", "component"} <= set(i["status"])):
            raise Malformed(f"{where}: input {i['name']}: status needs subject and component")
    for k in ("id", "shown", "where", "recorded_by"):
        if not isinstance(rec[k], str):
            raise Malformed(f"{where}: {k} must be a string")
    for k in ("grade_shown", "supersedes", "note"):
        if rec.get(k) is not None and not isinstance(rec[k], str):
            raise Malformed(f"{where}: {k} must be a string or null")
    claims = rec.get("operator_claims")
    if claims is not None and not isinstance(claims, list):
        raise Malformed(f"{where}: operator_claims must be a list")
    for i in rec["inputs"]:
        if not isinstance(i["name"], str):
            raise Malformed(f"{where}: input names must be strings")
        if "alternatives" in i and not isinstance(i["alternatives"], list):
            raise Malformed(f"{where}: input {i['name']}: alternatives must be a list")
        if isinstance(i.get("pending"), dict) and "value" not in i["pending"]:
            raise Malformed(f"{where}: input {i['name']}: pending needs a value")
    for a in op["args"]:
        if a not in names:
            raise Malformed(f"{where}: op uses {a!r}, which is not an input")
    disp = rec["display"]
    if not isinstance(disp, dict) or disp.get("as") not in SHOWN_AS or "value" not in disp:
        raise Malformed(f"{where}: display needs as (one of {sorted(SHOWN_AS)}) and value")
    if not isinstance(disp["value"], str):
        raise Malformed(f"{where}: display.value must be a string")
    dec = disp.get("decimals", 0)
    if isinstance(dec, bool) or not isinstance(dec, int) or not 0 <= dec <= 12:
        raise Malformed(f"{where}: display.decimals must be a whole number from 0 to 12")
    for c in rec.get("operator_claims") or []:
        if not isinstance(c, dict) or c.get("says") not in OPERATORS or "by" not in c:
            raise Malformed(f"{where}: each operator claim needs by and says")
    if not (isinstance(rec["recorded_on"], str) and DATE.fullmatch(rec["recorded_on"])):
        raise Malformed(f"{where}: recorded_on is not YYYY-MM-DD")
    try:
        dt.date.fromisoformat(rec["recorded_on"])
    except ValueError:
        raise Malformed(f"{where}: recorded_on is not a date")
    # Every input combination must be computable: a bad value is malformed,
    # not a finding.
    try:
        for i in rec["inputs"]:
            for v in candidates(i) + ([i["pending"]["value"] if isinstance(i["pending"], dict) else i["pending"]] if "pending" in i else []):
                _typed(v)
        compute(rec)
    except Malformed as e:
        raise Malformed(f"{where}: {e}")


# --- the operations ----------------------------------------------------------------

def _typed(v):
    """Check that a value is one the operations take."""
    if isinstance(v, list):
        if not all(isinstance(x, str) for x in v):
            raise Malformed(f"list items must be strings: {v!r}")
        return
    if isinstance(v, str) and (DATE.fullmatch(v) or TIME.fullmatch(v)):
        return _time(v) if "T" in v else _date(v)
    _num(v)


def _date(v):
    if isinstance(v, str) and DATE.fullmatch(v):
        try:
            return dt.date.fromisoformat(v)
        except ValueError:
            pass
    raise Malformed(f"not a date: {v!r}")


def _time(v):
    if isinstance(v, str) and TIME.fullmatch(v):
        try:
            return dt.datetime.fromisoformat(v)
        except ValueError:
            pass
    raise Malformed(f"not a time: {v!r}")


def _num(v):
    if isinstance(v, bool) or not isinstance(v, (int, float, str)):
        raise Malformed(f"not a number: {v!r}")
    try:
        d = Decimal(str(v))
    except (InvalidOperation, ValueError):
        raise Malformed(f"not a number: {v!r}")
    if not d.is_finite():
        raise Malformed(f"not a finite number: {v!r}")
    if abs(d) >= Decimal(10) ** 15:
        raise Malformed(f"number too large: {v!r}")
    return d


def add_months(day, months):
    """Calendar months, as a period 'n months from publication' is read.
    The day of the month is kept where it exists, else the month's last day."""
    m = day.month - 1 + months
    y, m = day.year + m // 12, m % 12 + 1
    return dt.date(y, m, min(day.day, calendar.monthrange(y, m)[1]))


def apply(kind, a, b):
    if kind == "divide":
        d = _num(b)
        if d == 0:
            raise Malformed("division by zero")
        return _num(a) / d
    if kind == "add_months":
        n = _num(b)
        if n != int(n):
            raise Malformed(f"add_months takes whole months: {b!r}")
        return add_months(_date(a), int(n))
    if kind == "days_between":
        return Decimal((_date(b) - _date(a)).days)
    if kind == "minutes_between":
        return Decimal(int((_time(b) - _time(a)).total_seconds() // 60))
    if kind == "count":
        if not isinstance(a, list) or not isinstance(b, list):
            raise Malformed("count takes two lists: items and exclusions")
        return Decimal(len(set(a) - set(b)))
    raise Malformed(f"unknown operation {kind}")


def render(value, display):
    """The value as it would be shown, at the precision the text shows it."""
    how = display["as"]
    if how in ("month", "day"):
        if not isinstance(value, dt.date):
            raise Malformed(f"display {how} needs a date")
        return value.strftime("%Y-%m") if how == "month" else value.isoformat()
    if isinstance(value, dt.date):
        raise Malformed(f"display {how} needs a number")
    if how == "hours_minutes":
        n = int(value)
        return f"{n // 60}:{n % 60:02d}"
    if how == "percent":
        value = value * 100
    places = int(display.get("decimals", 0))
    q = Decimal(1).scaleb(-places)
    return str(value.quantize(q, rounding=ROUND_HALF_UP))


def candidates(inp):
    """The value, its alternatives and the two ends of its range."""
    vals = [inp["value"]]
    vals += list(inp.get("alternatives") or [])
    if "range" in inp:
        vals += list(inp["range"])
    out = []
    for v in vals:
        if v not in out:
            out.append(v)
    return out


def compute(rec, override=None):
    inputs = {i["name"]: i["value"] for i in rec["inputs"]}
    inputs.update(override or {})
    a, b = (inputs[x] for x in rec["op"]["args"])
    return render(apply(rec["op"]["kind"], a, b), rec["display"])


# --- the check ---------------------------------------------------------------------

def check(rec, status=None, on=None):
    """One record → a dict: computed, verdict, flags, and the values behind them."""
    shown = str(rec["display"]["value"])
    computed = compute(rec)
    flags = []
    detail = {}

    # Inputs' ranges and alternatives, all combinations.
    names = rec["op"]["args"]
    by_name = {i["name"]: i for i in rec["inputs"]}
    seen = set()
    for combo in itertools.product(*(candidates(by_name[n]) for n in names)):
        seen.add(compute(rec, dict(zip(names, combo))))
    if len(seen) > 1:
        flags.append("sensitive")
        detail["over_inputs"] = sorted(seen)
    else:
        detail["robust"] = True

    pend = {}
    for i in rec["inputs"]:
        if "pending" in i:
            p = i["pending"]
            pval = p["value"] if isinstance(p, dict) else p
            pend[i["name"]] = compute(rec, {i["name"]: pval})
    changed = {k: v for k, v in pend.items() if v != computed}
    if changed:
        flags.append("if-pending")
        detail["if_pending"] = changed

    op = rec["operator"]
    grade = rec.get("grade_shown")
    if op == "unknown":
        flags.append("operator-unknown")
    elif op != "source" and grade and shows_a(grade) and not marked(grade, rec["shown"]):
        flags.append("grade-borrowed")
    claims = {c["says"] for c in rec.get("operator_claims") or []}
    if op != "unknown" and claims:
        claims.add(op)
    if len(claims) > 1:
        flags.append("claims-disagree")
        detail["claims"] = [f"{c['by']}: {c['says']}" for c in rec["operator_claims"]]

    if status is not None and on is not None:
        for i in rec["inputs"]:
            s = i.get("status")
            if not s:
                continue
            ans = statuslog.current(status, s["subject"], s["component"], on)
            if ans["status"] == "expired":
                flags.append("input-expired")
                detail.setdefault("expired", []).append(f"{i['name']}: {ans['assertion']['id']}")
            elif ans["status"] == "no-record":
                flags.append("input-unrecorded")
                detail.setdefault("unrecorded", []).append(i["name"])
            else:
                detail.setdefault("status", []).append(
                    f"{i['name']}: {ans['assertion']['id']} ({ans['status']}"
                    + (f", expires {ans['assertion']['expires_on']})" if ans["assertion"].get("expires_on") else ")"))

    return {"id": rec["id"], "shown": rec["shown"], "where": rec["where"],
            "computed": computed, "displayed": shown,
            "verdict": "recomputes" if computed == shown else "differs",
            "operator": op, "flags": flags, "detail": detail}


def check_log(records):
    problems = []
    ids = set()
    replaced = set()
    for n, r in enumerate(records, start=1):
        if r["id"] in ids:
            problems.append(f"record {n}: id {r['id']} is used twice")
        if r.get("supersedes") and r["supersedes"] not in ids:
            problems.append(f"record {n}: supersedes {r['supersedes']}, not recorded earlier")
        if r.get("supersedes") and r["supersedes"] in replaced:
            problems.append(f"record {n}: {r['supersedes']} is already superseded by another record")
        if r.get("supersedes"):
            replaced.add(r["supersedes"])
        ids.add(r["id"])
    return problems


def current_records(records):
    """Records not replaced by a later one."""
    replaced = {r["supersedes"] for r in records if r.get("supersedes")}
    return [r for r in records if r["id"] not in replaced]


def report(results):
    lines = []
    for r in results:
        head = f"{r['id']}  {r['verdict']:<10} shown {r['displayed']!s:<8} computed {r['computed']!s:<8} operator {r['operator']}"
        lines.append(head)
        lines.append(f"    {r['shown']}  — {r['where']}")
        if r["flags"]:
            lines.append("    flags: " + ", ".join(r["flags"]))
        d = r["detail"]
        if "over_inputs" in d:
            lines.append("    over the inputs' ranges and alternatives: " + ", ".join(d["over_inputs"]))
        elif d.get("robust"):
            lines.append("    robust to the inputs' ranges and alternatives")
        for k, v in (d.get("if_pending") or {}).items():
            lines.append(f"    if {k} takes its pending value: {v}")
        for c in d.get("claims") or []:
            lines.append(f"    who computed it, according to {c}")
        for s in d.get("status") or []:
            lines.append(f"    status: {s}")
        for s in d.get("expired") or []:
            lines.append(f"    expired: {s}")
        for s in d.get("unrecorded") or []:
            lines.append(f"    no status-log line for input {s}")
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--log", required=True, help="register/computed.jsonl")
    p.add_argument("--status", help="register/status_log.jsonl")
    p.add_argument("--on", help="YYYY-MM-DD (with --status)")
    p.add_argument("--all", action="store_true", help="include records replaced by later ones")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    try:
        records = load(args.log)
        if bool(args.status) != bool(args.on):
            raise Malformed("--status and --on go together")
        status = statuslog.load(args.status) if args.status else None
        if args.on and not DATE.fullmatch(args.on):
            raise Malformed("--on is not YYYY-MM-DD")
        if args.on:
            dt.date.fromisoformat(args.on)
        for n, a in enumerate(status or [], start=1):
            if not isinstance(a, dict) or not {"id", "subject", "component", "recorded_on"} <= set(a):
                raise Malformed(f"status log line {n}: needs id, subject, component and recorded_on")
        problems = check_log(records)
        for msg in problems:
            print("problem:", msg, file=sys.stderr)
        if problems:
            return 2
        chosen = records if args.all else current_records(records)
        results = [check(r, status, args.on) for r in chosen]
    except Malformed as e:
        print("error:", e, file=sys.stderr)
        return 2
    except (OSError, ValueError, TypeError, KeyError, ArithmeticError) as e:
        print("error:", repr(e), file=sys.stderr)
        return 2
    print(json.dumps(results, ensure_ascii=False, indent=2) if args.json else report(results))
    return 1 if any(r["verdict"] != "recomputes" or r["flags"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
