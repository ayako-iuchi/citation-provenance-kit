#!/usr/bin/env python3
"""loci — split a chapter into the places a citation can point to.

A retrieval pipeline can audit only what it can name. If the unit it indexes is a
fixed-size window of text, a citation cannot say which paragraph it rests on, and a
footnote printed at the foot of a page travels with whatever sentence it happens
to sit under. This tool cuts a chapter into loci instead:

    paragraph   a numbered paragraph ("6.22 ..."), which may run across pages
    heading     a lettered section heading ("(c) ..."), which is a locus of its own
    footnote    a footnote, kept apart and linked to the locus that carries its marker

Each locus records the printed pages it spans, and its words as a kit v1.3
snapshot (words + SHA-256, written once). Page heads are dropped.

It reads the line geometry written by pdflines.py. A footnote number is a line
of digits much shorter than body text whose number also appears as a superscript
marker in the body of the same page. A line is a footnote line if it sits in the
footnote zone at the foot of the page (from the first footnote number down) and is
shorter than body text.

Limits. It knows paragraphs, lettered headings and footnotes, nothing else.
Tables, figures, captions, source lines and capitalised headings are not
recognised: given a whole page, they are appended to the paragraph before them.
The example therefore runs on lines excerpted by hand (examples/es2021_ch6/).
HEAD_ZONE is the height of the page heads of that one PDF. Line-end hyphens are
kept as printed ("poli- cies"), so a quotation that rejoins them will not match.

Usage:
    python3 loci.py LINES.json [--read-on YYYY-MM-DD] > loci.jsonl
    python3 loci.py LINES.json --naive          # what a text-only splitter makes of it

Standard library only. CC0 1.0. Part of the citation provenance kit (v1.4).
"""
import argparse
import hashlib
import json
import re
import sys
from collections import Counter

PARA = re.compile(r"^(\d+\.\d+)\s")
HEAD = re.compile(r"^\(([a-z])\)\s")
SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹"
MARKER = re.compile("[" + SUP + "]+")
HEAD_ZONE = 55.0  # page heads (running title, page number) sit above this y


def _sup_to_int(s):
    return int("".join(str(SUP.index(c)) for c in s))


def _body_height(pages):
    c = Counter(l["h"] for p in pages for l in p["lines"])
    return c.most_common(1)[0][0]


def classify(page, body_h):
    """Label each line of one page: head, footnote-number, footnote, body."""
    lines = page["lines"]
    marked = {_sup_to_int(s) for l in lines if l["h"] >= body_h - 1 for s in MARKER.findall(l["text"])}
    numbers = [l for l in lines if l["text"].isdigit() and l["h"] < 0.6 * body_h and l["y"] >= HEAD_ZONE
               and int(l["text"]) in marked]
    zone = min((l["y"] for l in numbers), default=None)
    out = []
    for l in lines:
        if l["y"] < HEAD_ZONE:
            kind = "head"
        elif l in numbers:
            kind = "footnote-number"
        elif zone is not None and l["y"] >= zone - 2 and l["h"] < body_h - 1:
            kind = "footnote"
        else:
            kind = "body"
        out.append((kind, l))
    return out


def _snapshot(doc, lid, label, pages, words, read_on):
    wording = " ".join(words)
    span = f"printed p. {pages[0]}" if len(pages) == 1 else f"printed pp. {pages[0]}–{pages[-1]}"
    return {
        "id": lid,
        "source": {k: doc["source"][k] for k in ("issuer", "title", "url") if k in doc["source"]},
        "edition": doc["edition"],
        "locus": f"{label}, {span}",
        "wording": wording,
        "wording_sha256": hashlib.sha256(wording.encode("utf-8")).hexdigest(),
        "read_on": read_on,
    }


def split(doc, prefix="es2021-ch6", read_on=None):
    """Return the loci of `doc` (the JSON written by pdflines.py), in reading order."""
    body_h = _body_height(doc["pages"])
    loci, cur, notes = [], None, []

    def close():
        if cur is not None:
            loci.append(cur)

    for page in doc["pages"]:
        pno = page["printed_page"]
        lines = classify(page, body_h)
        numbers = sorted((l["y"], int(l["text"])) for k, l in lines if k == "footnote-number")
        for kind, l in lines:
            text = l["text"]
            if kind in ("head", "footnote-number"):
                continue
            if kind == "footnote":
                n = max((num for y, num in numbers if y <= l["y"] + 2), default=None)
                if notes and notes[-1]["n"] == n and notes[-1]["page"] == pno:
                    notes[-1]["words"].append(text)
                else:
                    notes.append({"n": n, "page": pno, "words": [text]})
                continue
            m, h = PARA.match(text), HEAD.match(text)
            if m or h:
                close()
                if m:
                    cur = {"id": f"{prefix}-p{m.group(1)}", "kind": "paragraph", "label": f"¶{m.group(1)}",
                           "pages": [pno], "words": [text]}
                else:
                    cur = {"id": f"{prefix}-h{pno}{h.group(1)}", "kind": "heading",
                           "label": f"Section heading ({h.group(1)})", "pages": [pno], "words": [text]}
                continue
            if cur is None:
                continue  # text before the first locus of an excerpt
            if pno not in cur["pages"]:
                cur["pages"].append(pno)
            cur["words"].append(text)
    close()

    out = []
    for c in loci:
        marks = sorted({_sup_to_int(s) for s in MARKER.findall(" ".join(c["words"]))})
        out.append({"id": c["id"], "kind": c["kind"], "label": c["label"], "printed_pages": c["pages"],
                    "footnotes": [f"{prefix}-fn{n}" for n in marks], "anchored_in": None,
                    "snapshot": _snapshot(doc, c["id"], c["label"], c["pages"], c["words"], read_on)})
    for fn in notes:
        fid = f"{prefix}-fn{fn['n']}"
        anchor = next((o["id"] for o in out if fid in o["footnotes"]), None)
        out.append({"id": fid, "kind": "footnote", "label": f"footnote {fn['n']}", "printed_pages": [fn["page"]],
                    "footnotes": [], "anchored_in": anchor,
                    "snapshot": _snapshot(doc, fid, f"footnote {fn['n']}", [fn["page"]], fn["words"], read_on)})
    return out


def naive(doc):
    """What a text-only splitter makes of the same lines: no geometry, cut at paragraph numbers.

    Every line is kept in the order given, page heads and footnotes included, and each
    chunk is labelled with the page on which it starts.
    """
    chunks, cur = [], None
    for page in doc["pages"]:
        for l in page["lines"]:
            m = PARA.match(l["text"])
            if m:
                cur = {"label": f"¶{m.group(1)}", "page": page["printed_page"], "words": []}
                chunks.append(cur)
            if cur is not None:
                cur["words"].append(l["text"])
    return [{"label": c["label"], "page": c["page"], "text": " ".join(c["words"])} for c in chunks]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lines")
    ap.add_argument("--read-on", default=None)
    ap.add_argument("--naive", action="store_true")
    args = ap.parse_args(argv)
    with open(args.lines, encoding="utf-8") as f:
        doc = json.load(f)
    rows = naive(doc) if args.naive else split(doc, read_on=args.read_on)
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
