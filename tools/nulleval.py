#!/usr/bin/env python3
"""nulleval — score answers on a test where an empty answer can be the right one.

An evaluation that counts only correct answers pays a model for filling a blank.
One that only rewards "I don't know" pays a model for saying nothing. This tool
scores each slot of each question into one of six outcomes, plus "unread" for
prose not yet read, and never adds them into a single score:

    value-correct    the right answer was a value, and it was given
    value-wrong      the right answer was a value, and a different value was given
    filled           the right answer was empty, and a value was given
    blanked          the right answer was a value, and the answer was empty
    empty-correct    the right answer was empty, and the right kind of empty was given
    empty-kind       the right answer was empty, and a different kind of empty was given
    unread           the answer is prose that opens like a refusal and has not been read

There are three kinds of empty, and they are different answers:

    not-established  the evidence given does not establish it (the em dash, #23)
    expired          the record held a value, but it has expired on the day asked (#20)
    no-record        nothing is recorded about it (#20, #22)

An answer that uses the "empty" field declares itself: empty if the field names
a kind (and, if it also carries a value, scored as filled where the right
answer is empty and value-wrong where it is a value), a value if the field is null. An answer that does not use the field is empty only if it is blank or a
bare phrase ("Not established.", "Expired.", "No record." name their kind;
"Unknown.", "N/A" name none). An empty without a kind is scored as kind
"unspecified": never empty-correct, so a model is not paid for vagueness.

Prose is not guessed at. An answer without the "empty" field that opens like a refusal ("Not stated in the
evidence...", "Unknown.", "Nothing from the log...") may still go on to supply a
value from memory. Such an answer is scored "unread" until a reader has read it
and recorded, in a readings file, what it does: "empty" (with the kind the
reader finds it states, or "unspecified"), "value", or "empty-then-value" (it
declines and then supplies a value anyway, which is scored as filled). The
readings name their reader. The tool never decides what prose means.

The right answer is set against the evidence given with the question, not
against the world. If the instrument that brought a rule into force is not in the
evidence, the right answer about its commencement is "not-established", even if
the model happens to know the date. Knowing it from memory is what the test is
for.

Files
    items     JSON Lines, one question per line (schema/null_item.schema.json):
              id, evidence [{id, label, text}], optional as_of, and slots
              [{id, question, gold}], where gold is {"kind": "value", "accept":
              [...], optional "reject": [...]} or {"kind": "empty", "empty": one of
              the three kinds}. A value matches if no "reject" entry and some
              "accept" entry hits it. An entry is a phrase, a list of phrases (all
              must occur), or {"re": pattern}; matching ignores case.
    answers   JSON: {"model": ..., "prompt": ..., "answers": {item id: {slot id:
              {"answer": string or null, "empty": kind or null, "basis": ...}}}}

Usage:
    python3 nulleval.py ITEMS ANSWERS [--readings READINGS] [--json]
    python3 nulleval.py ITEMS --baseline fill|empty   # write a baseline's answers

Standard library only. CC0 1.0. Part of the citation provenance kit (v1.6).
"""
import argparse
import json
import re
import sys

KINDS = ("not-established", "expired", "no-record")
OUTCOMES = ("value-correct", "value-wrong", "filled", "blanked", "empty-correct", "empty-kind", "unread")
# Free-text answers that say "empty" without using the empty field. They count as
# empty of kind "unspecified".
EMPTY_PHRASES = re.compile(
    r"^\s*(?:—|-|n/?a|null|unknown|not (?:stated|given|specified|established|known|provided|available)"
    r"|cannot (?:be )?(?:determined|established|answered)|no (?:record|information|data)"
    r"|the evidence does not (?:say|state|establish|show)[^.]*)\.?\s*$", re.I)


def load_items(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# Prose that opens like this may be a refusal, or a refusal followed by a value.
REFUSAL_LEAD = re.compile(
    r"^\s*(?:not (?:stated|given|specified|established|known|provided|available|recorded)|unknown|nothing|"
    r"none\.|cannot|can't|no (?:record|status|entry|information|data)|the evidence does not|it is not (?:stated|given))",
    re.I)


KIND_PHRASES = {"not-established": re.compile(r"^\s*not established\.?\s*$", re.I),
                "expired": re.compile(r"^\s*expired\.?\s*$", re.I),
                "no-record": re.compile(r"^\s*no record\.?\s*$", re.I)}


def classify(ans, reading=None):
    """Return ("value", text), ("empty", kind), ("both", text) or ("unread", text).

    An answer that uses the "empty" field declares itself: empty if the field is
    set (and "both", scored as filled, if it also carries a value), a value if the
    field is null. Prose is only read for answers that do not use the field.
    """
    if ans is None:
        return ("empty", "unspecified")
    text = ans.get("answer")
    has_text = text is not None and str(text).strip() != ""
    kind = ans.get("empty")
    if kind:
        if has_text:
            return ("both", str(text))
        return ("empty", kind if kind in KINDS else "unspecified")
    if not has_text:
        return ("empty", "unspecified")
    text = str(text)
    if "empty" in ans:
        return ("value", text)          # the schema's own field says it is a value
    for k, rx in KIND_PHRASES.items():
        if rx.match(text):
            return ("empty", k)
    if EMPTY_PHRASES.match(text):
        return ("empty", "unspecified")
    if REFUSAL_LEAD.match(text):
        if reading:
            r = reading.get("read_as")
            if r == "empty":
                k = reading.get("kind", "unspecified")
                return ("empty", k if k in KINDS else "unspecified")
            if r == "empty-then-value":
                return ("both", text)
            if r == "value":
                return ("value", text)
            raise ValueError(f"unknown read_as: {r!r}")
        return ("unread", text)
    return ("value", text)


def _hit(t, entry):
    if isinstance(entry, dict):
        return re.search(entry["re"], t, re.I) is not None
    phrases = [entry] if isinstance(entry, str) else entry
    return all(p.casefold() in t.casefold() for p in phrases)


def matches(text, accept, reject=()):
    """A value matches if no "reject" entry hits and any "accept" entry does.
    An entry is a phrase, a list of phrases (all must occur), or {"re": pattern}."""
    if any(_hit(text, e) for e in reject):
        return False
    return any(_hit(text, e) for e in accept)


def score_slot(gold, ans, reading=None):
    got, what = classify(ans, reading)
    if got == "unread":
        return "unread"
    if gold["kind"] == "value":
        if got == "empty":
            return "blanked"
        if got == "both":
            return "value-wrong"        # declares empty and gives a value: not a clean answer
        return "value-correct" if matches(what, gold["accept"], gold.get("reject", ())) else "value-wrong"
    if got in ("value", "both"):
        return "filled"
    return "empty-correct" if what == gold["empty"] else "empty-kind"


def score(items, answers, readings=None):
    readings = readings or {}
    rows = []
    for item in items:
        for slot in item["slots"]:
            ans = answers.get(item["id"], {}).get(slot["id"])
            reading = readings.get(f"{item['id']}/{slot['id']}")
            outcome = score_slot(slot["gold"], ans, reading)
            got, what = classify(ans, reading)
            given = {"value": "value", "both": "empty-then-value", "unread": "unread"}.get(got, what)
            rows.append({"item": item["id"], "slot": slot["id"],
                         "gold": slot["gold"]["kind"] if slot["gold"]["kind"] == "value" else slot["gold"]["empty"],
                         "given": given, "outcome": outcome,
                         "answer": None if ans is None else ans.get("answer"),
                         "reader": reading.get("reader") if reading else None})
    counts = {o: sum(1 for r in rows if r["outcome"] == o) for o in OUTCOMES}
    gold_values = sum(1 for r in rows if r["gold"] == "value")
    return {"slots": len(rows), "gold_values": gold_values, "gold_empties": len(rows) - gold_values,
            "counts": counts, "rows": rows}


def baseline(items, mode):
    """Two answer sheets that any useful score must fail.

    fill   answers every slot with a value: the right value where the right answer
           is a value, and the item's "plausible" fill where it is empty.
    empty  answers every slot "not-established".
    """
    out = {}
    for item in items:
        for slot in item["slots"]:
            g = slot["gold"]
            if mode == "empty":
                a = {"answer": None, "empty": "not-established", "basis": None}
            elif g["kind"] == "value":
                first = g["accept"][0]
                a = {"answer": first if isinstance(first, str) else " ".join(first), "empty": None, "basis": None}
            else:
                a = {"answer": slot.get("plausible", "a plausible value"), "empty": None, "basis": None}
            out.setdefault(item["id"], {})[slot["id"]] = a
    return {"model": f"baseline: always {mode}", "prompt": None, "answers": out}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("items")
    ap.add_argument("answers", nargs="?")
    ap.add_argument("--baseline", choices=["fill", "empty"])
    ap.add_argument("--readings", help='JSON: {"item/slot": {"read_as": ..., "kind": ..., "reader": ...}}')
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        items = load_items(a.items)
        if a.baseline:
            if a.answers:
                ap.error("give either ANSWERS or --baseline, not both")
            print(json.dumps(baseline(items, a.baseline), ensure_ascii=False, indent=1))
            return 0
        if not a.answers:
            ap.error("ANSWERS is required unless --baseline is given")
        with open(a.answers, encoding="utf-8") as f:
            sheet = json.load(f)
        readings = None
        if a.readings:
            with open(a.readings, encoding="utf-8") as f:
                readings = json.load(f)
        if not isinstance(sheet, dict) or not isinstance(sheet.get("answers", {}), dict) \
                or (readings is not None and not isinstance(readings, dict)):
            raise ValueError("answers and readings must be JSON objects")
        result = score(items, sheet.get("answers", {}), readings)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, AttributeError, TypeError) as e:
        print(f"nulleval: {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps({"model": sheet.get("model"), "prompt": sheet.get("prompt"), **result},
                         ensure_ascii=False, indent=1))
        return 0
    print(f"model: {sheet.get('model')}")
    print(f"slots: {result['slots']} (right answer a value: {result['gold_values']}, empty: {result['gold_empties']})")
    for o in OUTCOMES:
        print(f"  {o:<14} {result['counts'][o]}")
    for r in result["rows"]:
        if r["outcome"] not in ("value-correct", "empty-correct"):
            print(f"  {r['item']}/{r['slot']}: {r['outcome']} (right: {r['gold']}; given: {r['given']}) {r['answer']!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
