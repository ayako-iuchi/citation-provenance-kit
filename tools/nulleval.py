#!/usr/bin/env python3
"""nulleval — score answers on a test where an empty answer can be the right one.

An evaluation that counts only correct answers pays a model for filling a blank.
One that only rewards "I don't know" pays a model for saying nothing. This tool
scores each slot of each question into one of six outcomes and never adds them
into a single score:

    value-correct    the right answer was a value, and it was given
    value-wrong      the right answer was a value, and a different value was given
    filled           the right answer was empty, and a value was given
    blanked          the right answer was a value, and the answer was empty
    empty-correct    the right answer was empty, and the right kind of empty was given
    empty-kind       the right answer was empty, and a different kind of empty was given

There are three kinds of empty, and they are different answers:

    not-established  the evidence given does not establish it (the em dash, #23)
    expired          the record held a value, but it has expired on the day asked (#20)
    no-record        nothing is recorded about it (#20, #22)

An answer that is empty without saying which kind is scored as kind "unspecified":
never empty-correct, so a model is not paid for vagueness.

The right answer is set against the evidence given with the question, not
against the world. If the instrument that brought a rule into force is not in the
evidence, the right answer about its commencement is "not-established", even if
the model happens to know the date. Knowing it from memory is what the test is
for.

Files
    items     JSON Lines, one question per line (schema/null_item.schema.json):
              id, evidence [{id, label, text}], optional as_of, and slots
              [{id, question, gold}], where gold is {"kind": "value", "accept":
              [phrases]} or {"kind": "empty", "empty": one of the three kinds}.
              A value matches if every phrase of any one entry of "accept" is in
              the answer (case-insensitive; an entry is a phrase or a list of them).
    answers   JSON: {"model": ..., "prompt": ..., "answers": {item id: {slot id:
              {"answer": string or null, "empty": kind or null, "basis": ...}}}}

Usage:
    python3 nulleval.py ITEMS ANSWERS [--json]
    python3 nulleval.py ITEMS --baseline fill|empty   # write a baseline's answers

Standard library only. CC0 1.0. Part of the citation provenance kit (v1.6).
"""
import argparse
import json
import re
import sys

KINDS = ("not-established", "expired", "no-record")
OUTCOMES = ("value-correct", "value-wrong", "filled", "blanked", "empty-correct", "empty-kind")
# Free-text answers that say "empty" without using the empty field. They count as
# empty of kind "unspecified".
EMPTY_PHRASES = re.compile(
    r"^\s*(?:—|-|n/?a|null|unknown|not (?:stated|given|specified|established|known|provided|available)"
    r"|cannot (?:be )?(?:determined|established|answered)|no (?:record|information|data)"
    r"|the evidence does not (?:say|state|establish|show)[^.]*)\.?\s*$", re.I)


def load_items(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def classify(ans):
    """Return ("value", text) or ("empty", kind) for one answer record."""
    if ans is None:
        return ("empty", "unspecified")
    kind = ans.get("empty")
    if kind:
        return ("empty", kind if kind in KINDS else "unspecified")
    text = ans.get("answer")
    if text is None or not str(text).strip() or EMPTY_PHRASES.match(str(text)):
        return ("empty", "unspecified")
    return ("value", str(text))


def matches(text, accept):
    t = text.casefold()
    for entry in accept:
        phrases = [entry] if isinstance(entry, str) else entry
        if all(p.casefold() in t for p in phrases):
            return True
    return False


def score_slot(gold, ans):
    got, what = classify(ans)
    if gold["kind"] == "value":
        if got == "empty":
            return "blanked"
        return "value-correct" if matches(what, gold["accept"]) else "value-wrong"
    if got == "value":
        return "filled"
    return "empty-correct" if what == gold["empty"] else "empty-kind"


def score(items, answers):
    rows = []
    for item in items:
        for slot in item["slots"]:
            ans = answers.get(item["id"], {}).get(slot["id"])
            outcome = score_slot(slot["gold"], ans)
            got, what = classify(ans)
            rows.append({"item": item["id"], "slot": slot["id"],
                         "gold": slot["gold"]["kind"] if slot["gold"]["kind"] == "value" else slot["gold"]["empty"],
                         "given": "value" if got == "value" else what,
                         "outcome": outcome,
                         "answer": None if ans is None else ans.get("answer")})
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
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        items = load_items(a.items)
        if a.baseline:
            print(json.dumps(baseline(items, a.baseline), ensure_ascii=False, indent=1))
            return 0
        if not a.answers:
            ap.error("ANSWERS is required unless --baseline is given")
        with open(a.answers, encoding="utf-8") as f:
            sheet = json.load(f)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"nulleval: {e}", file=sys.stderr)
        return 2
    result = score(items, sheet.get("answers", {}))
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
