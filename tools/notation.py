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
    component  = one of the ten names in csv/components.csv, English or Japanese,
                 or an extension the document declares (--extend; §4-2)
    open = "[" | "［" ;  close = "]" | "］" ;  bar = "|" | "｜" ;  colon = ":" | "："

A bracket is read only if it is a single grade, or names a known component
before a colon and grades at least one slot (A-D or a dash of any kind). Other
brackets ([sic], [LINK], [Note: ...], [page: 12], [A — a source]) are left
alone, and so are Markdown links whose label is a single grade ([A](url),
[A][ref], a line starting [A]: followed by a URL). A bare [B] in prose is read
as a plain grade: the text cannot tell it from one. An annotation may run
across a single line break, not across a blank line.

Checks (what a machine can see in the text):

    N0 malformed      a bracket names a component and grades it but does not
                      follow the grammar ([wording: A, page: B], [wording: A |],
                      [wording: A B]), or opens and closes with brackets of
                      different widths
                      (added in kit v1.5)
    N1 vocabulary    the component is not in the closed list (§4-2)
    N2 grade          the grade is not A-D or the em dash (§4-4)
    N3 dash           a null slot written with another dash (- – ‒ ― − ー －): a different
                      character is a different value to anything that reads it
    N4 slots          more than three slots (§4-5)
    N5 duplicate      the same component twice in one annotation (not in the paper;
                      added in kit v1.5)
    N6 no divergence  two or more slots, all with the same grade: write [A] (§4-5)
    N7 null first     the first slot, the one the claim rests on, is the em dash.
                      Not an error: the claim stands on something not established.
                      A plain [—] is reported the same way.
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
                                 [--markdown] [--extend NAME[=日本語名]]...

    --records   print every annotation as a JSON line (the typed records)
    --to        rewrite every well-formed annotation in the other language's
                form; the rest of the text, line endings included, is left as it is
    --markdown  skip fenced code blocks and inline code (not indented code blocks)
    --extend    declare an extension component; repeatable

Exit status, when checking (no --records, no --to): 1 if N0-N6 report
anything, 0 otherwise. 2 if the document cannot be read, in every mode.

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

BARRIER = "\x00"  # stands in for a blank line or masked code: an annotation never crosses it
CANDIDATE = re.compile(r"[\[［]([^\[\]［］\x00\n]{1,200}?)[\]］]")
NAME = r"[A-Za-z_\-぀-ヿ㐀-鿿]+"
SLOT = re.compile(r"^\s*(" + NAME + r")\s*[:：]\s*(\S+)\s*$")
LOOSE_NAME = re.compile(r"^\s*([^:：]+?)\s*[:：]")


def load_components(path=COMPONENTS_CSV, extend=()):
    """Return {name: (english_name, volatile)} for English and Japanese names.

    extend: extension components declared by the document, as "name" or
    "name=日本語名" (§4-2). Their volatility is not known, so it is None.
    """
    table = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            en, ja = row["component"].strip(), row["ja"].strip()
            volatile = row["can_become_false_without_document_changing"].strip().lower().startswith("yes")
            table[en] = (en, volatile)
            table[ja] = (en, volatile)
    for decl in extend:
        en, _, ja = decl.partition("=")
        table[en.strip()] = (en.strip(), None)
        if ja.strip():
            table[ja.strip()] = (en.strip(), None)
    return table


def _ja_names(path=COMPONENTS_CSV, extend=()):
    with open(path, encoding="utf-8-sig", newline="") as f:
        names = {row["component"].strip(): row["ja"].strip() for row in csv.DictReader(f)}
    for decl in extend:
        en, _, ja = decl.partition("=")
        if ja.strip():
            names[en.strip()] = ja.strip()
    return names


def _line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def _mask_fences(v):
    """Mask fenced code blocks as CommonMark reads them: the closing fence uses
    the opening character, at least as many times; an unclosed fence runs to
    the end of the document. Indented code blocks are not recognised."""
    out, pos, fence = [], 0, None
    for line in v.splitlines(keepends=True):
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        m = re.match(r"(`{3,}|~{3,})", stripped) if indent <= 3 else None
        if fence is None:
            if m and not (m.group(1)[0] == "`" and "`" in stripped[len(m.group(1)):]):
                fence = m.group(1)
                out.append(BARRIER * len(line.rstrip("\r\n")) + line[len(line.rstrip("\r\n")):])
            else:
                out.append(line)
        else:
            body = line.rstrip("\r\n")
            out.append(BARRIER * len(body) + line[len(body):])
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) \
                    and stripped[len(m.group(1)):].strip() == "":
                fence = None
    return "".join(out)


def _view(text, markdown=False):
    """A copy of text, the same length, in which an annotation can be found
    across a single line break (as in text taken from a PDF) but not across a
    blank line, and, with markdown=True, not inside code."""
    v = text
    if markdown:
        v = _mask_fences(v)
        # Inline code: a run of backticks closed by the same run, not across a
        # blank line. An unmatched backtick masks nothing.
        v = re.sub(r"(`+)((?:(?!\n[ \t\r]*\n)[^`])+?)\1",
                   lambda m: BARRIER * len(m.group(0)), v)
    v = re.sub(r"\n(?=[ \t\r]*\n)", BARRIER, v)
    return v.replace("\r", " ").replace("\n", " ")


def _scan(text, components, markdown=False):
    """Yield (start, end, record) for every annotation, including malformed ones."""
    view = _view(text, markdown)
    for m in CANDIDATE.finditer(view):
        inner = m.group(1)
        raw = " ".join(inner.split())
        line = _line_of(text, m.start())
        wide = text[m.start()] == "［"
        if raw in GRADES:
            # Only a bracket this short can be a Markdown link label; one that
            # names a component is read whatever follows it.
            before = view[m.start() - 1] if m.start() else ""
            rest = view[m.end():m.end() + 40]
            at_line_start = text[:m.start()].rsplit("\n", 1)[-1].strip() == ""
            if not wide and ((before and before in "]!") or rest[:1] in ("(", "[")
                             or (at_line_start and re.match(r":\s*\S*[/.<]", rest))):
                continue  # a Markdown link, image or reference definition
            text_ = ("［%s］" if wide else "[%s]") % raw
            yield m.start(), m.end(), {"line": line, "text": text_, "form": "plain",
                                       "slots": [{"component": None, "written": None, "grade": raw, "volatile": None}]}
            continue
        if ":" not in inner and "：" not in inner:
            continue
        parts = re.split(r"[|｜]", inner)
        names = [LOOSE_NAME.match(p) for p in parts]
        names = [n.group(1).strip() for n in names if n]
        if not any(n in components for n in names):
            continue  # not about any component: [Note: ...], [Edit: ...]
        if names and all(n in TEMPLATE_NAMES for n in names):
            continue  # the paper's statement of the form, [component: grade | ...]
        slots = []
        for part in parts:
            sm = SLOT.match(part)
            if not sm:
                slots = None
                break
            name, grade = sm.group(1), sm.group(2)
            known = components.get(name)
            slots.append({"component": known[0] if known else None, "written": name,
                          "grade": grade, "volatile": known[1] if known else None})
        full = " ".join(text[m.start():m.end()].split())
        grade_like = r"[:：]\s*([A-D\u2014" + "".join(re.escape(c) for c in WRONG_DASHES) + r"])(?![A-Za-z0-9])"
        if slots is not None and not any(s["grade"] in GRADES or s["grade"] in WRONG_DASHES for s in slots):
            continue  # names a component but grades nothing: [page: 12], ［日付: 2024年］
        if slots is None and not re.search(grade_like, inner):
            continue  # [edition: 3rd ed.]
        mixed = wide != (text[m.end() - 1] == "］")
        if slots is None or mixed:
            yield m.start(), m.end(), {"line": line, "text": full, "form": "malformed", "slots": []}
            continue
        ja_shape = wide or any(c in inner for c in "｜：") or any(
            re.search(r"[぀-ヿ㐀-鿿]", s["written"]) for s in slots)
        yield m.start(), m.end(), {"line": line, "text": full, "form": "ja" if ja_shape else "en", "slots": slots}


def parse(text, components=None, markdown=False):
    """Yield one record per annotation found in text.

    A bracket is read as an annotation if it is a single grade ([A]), or if at
    least one of its parts names a known component before a colon. A bracket
    that names a component but does not follow the grammar is yielded with
    form "malformed" (check N0). Anything else in brackets ([LINK], [sic],
    [Note: ...], [A — a source], Markdown links) is left alone.
    """
    components = components or load_components()
    for _, _, rec in _scan(text, components, markdown):
        yield rec


def check(record):
    """Return a list of (check, severity, detail) for one record."""
    if record["form"] == "malformed":
        return [("N0", "error", "names a component but does not follow the grammar")]
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
    if record["form"] != "plain":
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
        first = slots[0]["written"] or "the only grade"
        out.append(("N7", "notice", f"the first slot ({first}) is not established; the claim rests on it"))
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


def rewrite(text, lang, markdown=False, extend=()):
    """Return text with every well-formed annotation written in the given
    language's form. Everything else, line endings included, is left as it is."""
    ja_names = _ja_names(extend=extend)
    components = load_components(extend=extend)
    out, last = [], 0
    for start, end, rec in _scan(text, components, markdown):
        if rec["form"] == "malformed":
            continue
        out.append(text[last:start])
        out.append(render(rec, lang, ja_names))
        last = end
    out.append(text[last:])
    return "".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("document")
    ap.add_argument("--json", action="store_true", help="findings as JSON")
    ap.add_argument("--records", action="store_true", help="every annotation as a JSON line")
    ap.add_argument("--to", choices=["en", "ja"], help="rewrite annotations in this form")
    ap.add_argument("--markdown", action="store_true", help="skip code blocks and inline code")
    ap.add_argument("--extend", action="append", default=[], metavar="NAME[=日本語名]",
                    help="an extension component the document declares (§4-2); repeatable")
    a = ap.parse_args(argv)
    try:
        with open(a.document, encoding="utf-8", newline="") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"notation: cannot read {a.document}: {e}", file=sys.stderr)
        return 2
    if a.to:
        sys.stdout.write(rewrite(text, a.to, a.markdown, a.extend))
        return 0
    records = list(parse(text, load_components(extend=a.extend), a.markdown))
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
        print(f"{len(records)} annotation(s), {errors} error(s), {len(findings) - errors} notice(s)")
    return 1 if any(f_["severity"] == "error" for f_ in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
