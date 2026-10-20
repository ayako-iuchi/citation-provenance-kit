#!/usr/bin/env python3
"""pdflines — turn `pdftotext -bbox-layout` output into lines with their geometry.

A chunker that sees only text cannot tell a footnote from the paragraph it is
printed under, or a page head from a sentence. The geometry can: on the page
this kit uses as its example, body lines are about 15.8 points tall, footnote
lines about 13.1, and a footnote marker about 9. This tool keeps that.

Usage:
    pdftotext -f 10 -l 11 -bbox-layout chapter.pdf pages.html
    python3 pdflines.py pages.html --first-printed-page 188 > lines.json

Output (JSON):
    {"pages": [{"printed_page": 188, "lines": [{"y": 82.7, "h": 15.77, "text": "6.18 Since ..."}, ...]}, ...]}

A word much shorter than its line and made only of digits is a superscript
marker; it is written as "⁶" (Unicode superscript digits) and kept in the text.
Control characters are dropped (the example PDF puts a BEL after each footnote
number).
Lines are in reading order as pdftotext gives them. Standard library only.
CC0 1.0. Part of the citation provenance kit (v1.4).
"""
import argparse
import json
import sys
import unicodedata
from html.parser import HTMLParser

SUPERSCRIPT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
MARKER_RATIO = 0.75  # a digit word shorter than this share of its line is a marker


class _Bbox(HTMLParser):
    def __init__(self):
        super().__init__()
        self.pages, self._line, self._word, self._text = [], None, None, ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "page":
            self.pages.append([])
        elif tag == "line":
            self._line = {"y0": float(a["ymin"]), "y1": float(a["ymax"]), "words": []}
        elif tag == "word":
            self._word = (float(a["ymin"]), float(a["ymax"]))
            self._text = ""

    def handle_data(self, data):
        if self._word is not None:
            self._text += data

    def handle_endtag(self, tag):
        if tag == "word" and self._word is not None:
            text = "".join(c for c in self._text if unicodedata.category(c) != "Cc")
            self._line["words"].append((text, self._word[1] - self._word[0]))
            self._word = None
        elif tag == "line" and self._line is not None:
            self.pages[-1].append(self._line)
            self._line = None


def _line_text(line):
    h = line["y1"] - line["y0"]
    out = []
    for text, wh in line["words"]:
        if text.isdigit() and wh < MARKER_RATIO * h and out:
            out[-1] += text.translate(SUPERSCRIPT)
        else:
            out.append(text)
    return " ".join(out)


def parse(html, first_printed_page):
    p = _Bbox()
    p.feed(html)
    pages = []
    for i, lines in enumerate(p.pages):
        pages.append({
            "printed_page": first_printed_page + i,
            "lines": [{"y": round(l["y0"], 1), "h": round(l["y1"] - l["y0"], 2), "text": _line_text(l)}
                      for l in lines],
        })
    return {"pages": pages}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("bbox_html")
    ap.add_argument("--first-printed-page", type=int, required=True)
    args = ap.parse_args(argv)
    with open(args.bbox_html, encoding="utf-8") as f:
        out = parse(f.read(), args.first_printed_page)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
