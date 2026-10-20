#!/usr/bin/env python3
"""notation — read component-graded citation as typed records, and check its form.

The notation of *What Breaks in a Citation* (§4) is written inside a sentence:

    [wording: A | commencement: —]          English
    ［語: A｜施行: —］                        Japanese, the same shape

This tool reads both forms with one grammar and turns each annotation into a
record: a list of slots, each a component (a type from csv/components.csv) and
a grade. Three states are kept apart:

    a grade (A-D)     the component was established, by a source of that character
    the em dash (—)   the component was considered and not established; not asserted
    no slot           nothing is recorded about the component, either way

Grammar (whitespace between tokens is ignored; brackets, bars and colons may
be half- or full-width):

    annotation = open , slot , { bar , slot } , close
               | open , grade , close                     (* plain [A] *)
    slot       = component , colon , grade
    grade      = "A" | "B" | "C" | "D" | "—"               (* U+2014 *)
    component  = one of the ten names in csv/components.csv, English or Japanese
    open = "[" | "［" ;  close = "]" | "］" ;  bar = "|" | "｜" ;  colon = ":" | "："

Checks (what a machine can see in the text):

    N1 vocabulary     the component is not in the closed list (§4-2)
    N2 grade          the grade is not A-D or the em dash (§4-4)
    N3 dash           a null slot written with another dash (- – ― − ー －): a different
                      character is a different value to anything that reads it
    N4 slots          more than three slots (§4-5)
    N5 duplicate      the same component twice in one annotation (not in the paper;
                      added in kit v1.5)
    N6 no divergence  two or more slots, all with the same grade: write [A] (§4-5)
    N7 null first     the first slot, the one the claim rests on, is the em dash.
                      Not an error: the claim stands on something not established.
                      Reported as a notice; it does not change the exit status
                      (added in kit v1.5)

What it cannot check, and does not try to: whether the first slot is the one
the claim rests on (§4-3); whether a divergence carries weight (§4-5); whether
a component is applied as defined; whether a grade describes the source rather
than the author's confidence (§3-3); and what document a grade was given
against. Those stay with the person who writes the sentence.

Each slot also carries `volatile`: whether, per csv/components.csv, the
component can become false without the document changing (edition, existence,
commencement, dependency). The notation has no date. A grade on a volatile
component holds only for the day it was resolved, which belongs in the status
log (kit v1.3), not in the annotation.

Usage:
    python3 notation.py DOCUMENT [--json] [--records] [--to en|ja]

    --records   print every annotation as a JSON line (the typed records)
    --to        rewrite every annotation in the other language's form
                (the rest of the text is left as it is)

Exit status is 1 if N1-N6 report anything.

CC0 1.0. Part of the citation provenance kit (v1.5).
"""
import argparse
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMPONENTS_CSV = os.path.join(HERE, "..", "csv", "components.csv")

EM_DASH = "—"
WRONG_DASHES = {"-": "hyphen-minus", "–": "en dash", "―": "horizontal bar",
                "−": "minus sign", "ー": "katakana prolonged sound mark",
                "－": "fullwidth hyphen-minus", "‒": "figure dash"}
GRADES = {"A", "B", "C", "D", EM_DASH}
TEMPLATE_NAMES, TEMPLATE_GRADES = {"component", "成分"}, {"grade", "級"}

OPEN, CLOSE, BAR, COLON = "[［", "]］", "|｜", ":："
# An annotation candidate: brackets holding at least one "word : token" pair, or a lone grade.
CANDIDATE = re.compile(r"[\[［]([^\[\]［］\n]{1,200}?)[\]］]")
SLOT = re.compile(r"^\s*([^:：|｜]+?)\s*[:：]\s*(\S*?)\s*$")


def load_components(path=COMPONENTS_CSV):
    """Return {name: (english_name, volatile)} for English and Japanese names."""
    table = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            en, ja = row["component"].strip(), row["ja"].strip()
            volatile = row["can_become_false_without_document_changing"].strip().lower().startswith("yes")
            table[en] = (en, volatile)
            table[ja] = (en, volatile)
    return table


def _ja_names(path=COMPONENTS_CSV):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return {row["component"].strip(): row["ja"].strip() for row in csv.DictReader(f)}


def _line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def parse(text, components=None):
    """Yield one record per annotation found in text.

    A bracket counts as an annotation if every part between bars has the form
    `name: token`, or if it is a single grade on its own ([A]). Anything else
    in brackets ([LINK], [sic], [A — a source]) is left alone.
    """
    components = components or load_components()
    # Join lines so that an annotation broken across a line (as in text taken
    # from a PDF) is still read; positions map back to the original lines.
    flat = text.replace("\r\n", "\n")
    joined = re.sub(r"\s*\n\s*", lambda m: " " * len(m.group(0)), flat)
    for m in CANDIDATE.finditer(joined):
        inner = m.group(1)
        raw = flat[m.start():m.end()]
        parts = re.split(r"[|｜]", inner)
        if len(parts) == 1 and inner.strip() in GRADES | set(WRONG_DASHES):
            yield {"line": _line_of(flat, m.start()), "text": " ".join(raw.split()),
                   "form": "plain", "slots": [{"component": None, "written": None,
                                               "grade": inner.strip(), "volatile": None}]}
            continue
        slots = []
        for part in parts:
            sm = SLOT.match(part)
            if not sm:
                slots = None
                break
            name, grade = sm.group(1).strip(), sm.group(2).strip()
            if not re.fullmatch(r"[A-Za-z぀-ヿ㐀-鿿]+", name):
                slots = None
                break
            known = components.get(name)
            slots.append({"component": known[0] if known else None, "written": name,
                          "grade": grade, "volatile": known[1] if known else None})
        if not slots:
            continue
        if all(s["written"] in TEMPLATE_NAMES and s["grade"] in TEMPLATE_GRADES for s in slots):
            # The paper's own statement of the form, [component: grade | ...]: not an annotation.
            continue
        ja_shape = any(c in raw for c in "［］｜：") or any(
            re.search(r"[぀-ヿ㐀-鿿]", s["written"]) for s in slots)
        yield {"line": _line_of(flat, m.start()), "text": " ".join(raw.split()),
               "form": "ja" if ja_shape else "en", "slots": slots}


def check(record):
    """Return a list of (check, severity, detail) for one record."""
    out = []
    slots = record["slots"]
    for s in slots:
        if record["form"] != "plain" and s["component"] is None:
            out.append(("N1", "error", f'component "{s["written"]}" is not in the closed vocabulary'))
        g = s["grade"]
        if g in WRONG_DASHES:
            out.append(("N3", "error", f'null slot written with a {WRONG_DASHES[g]} (U+{ord(g):04X}), not the em dash (U+2014)'))
        elif g not in GRADES:
            out.append(("N2", "error", f'grade "{g}" is not A-D or the em dash'))
    if record["form"] == "plain":
        return out
    if len(slots) > 3:
        out.append(("N4", "error", f"{len(slots)} slots; three at most — split the claim, not the citation"))
    seen = set()
    for s in slots:
        key = s["component"] or s["written"]
        if key in seen:
            out.append(("N5", "error", f'component "{s["written"]}" appears twice'))
        seen.add(key)
    grades = [s["grade"] for s in slots]
    if len(grades) >= 2 and len(set(grades)) == 1 and grades[0] in GRADES:
        out.append(("N6", "error", f"every slot is {grades[0]}; write [{grades[0]}]"))
    if slots and slots[0]["grade"] == EM_DASH:
        out.append(("N7", "notice", f'the first slot ({slots[0]["written"]}) is not established; the claim rests on it'))
    return out


def render(record, lang, ja_names=None):
    """Write one record in the English or the Japanese form."""
    if record["form"] == "plain":
        g = record["slots"][0]["grade"]
        return f"[{g}]" if lang == "en" else f"［{g}］"
    ja_names = ja_names or _ja_names()
    parts = []
    for s in record["slots"]:
        name = s["component"] or s["written"]
        if lang == "ja":
            name = ja_names.get(name, name)
        parts.append(f"{name}: {s['grade']}")
    return "[" + " | ".join(parts) + "]" if lang == "en" else "［" + "｜".join(parts) + "］"


def rewrite(text, lang):
    """Return text with every annotation written in the given language's form."""
    ja_names = _ja_names()
    components = load_components()
    flat = text.replace("\r\n", "\n")
    joined = re.sub(r"\s*\n\s*", lambda m: " " * len(m.group(0)), flat)
    out, last = [], 0
    for m in CANDIDATE.finditer(joined):
        rec = next(parse(flat[m.start():m.end()], components), None)
        if rec is None:
            continue
        out.append(flat[last:m.start()])
        out.append(render(rec, lang, ja_names))
        last = m.end()
    out.append(flat[last:])
    return "".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("document")
    ap.add_argument("--json", action="store_true", help="findings as JSON")
    ap.add_argument("--records", action="store_true", help="every annotation as a JSON line")
    ap.add_argument("--to", choices=["en", "ja"], help="rewrite annotations in this form")
    a = ap.parse_args(argv)
    with open(a.document, encoding="utf-8") as f:
        text = f.read()
    if a.to:
        sys.stdout.write(rewrite(text, a.to))
        return 0
    records = list(parse(text))
    if a.records:
        for r in records:
            print(json.dumps(r, ensure_ascii=False))
        return 0
    findings = []
    for r in records:
        for c, sev, detail in check(r):
            findings.append({"check": c, "severity": sev, "line": r["line"], "text": r["text"], "detail": detail})
    if a.json:
        print(json.dumps({"annotations": len(records), "findings": findings}, ensure_ascii=False, indent=2))
    else:
        for f_ in findings:
            print(f'{a.document}:{f_["line"]}: {f_["check"]} {f_["severity"]}: {f_["detail"]}  {f_["text"]}')
        errors = sum(1 for f_ in findings if f_["severity"] == "error")
        notices = len(findings) - errors
        print(f"{len(records)} annotation(s), {errors} error(s), {notices} notice(s)")
    return 1 if any(f_["severity"] == "error" for f_ in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
