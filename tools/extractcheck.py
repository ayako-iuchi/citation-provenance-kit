#!/usr/bin/env python3
"""extractcheck — check a verbatim-extraction report for what it says without showing.

An extractor told to quote and not interpret usually does quote. Where the source
runs out (an item that is not there, a footnote that cannot be placed, a second
document), it tends to explain, and the explanation can carry facts the source
never gave: which notification inserted a provision, a formal title, a statutory
exemption. Written in the same report as the quotations, they read as extraction.

This tool cannot tell memory from the page. It can tell what a report shows from
what it only says. It reads a report in the form of schema/extraction.schema.json
and checks:

    X1  a quotation is not on the page given for it (only with --source)
    X2  an identifier in the extractor's own words is not shown by the report's
        verbatim text (quotations, footnotes, search record), not given by the
        request (the item as named), not in the source text (with --source), and
        not declared under "outside"
    X3  an item reported not in the source has no search record
    X4  an item reported found has no page

"The extractor's own words" are the remarks (per item and for the report), the
description of the source (title, issuer, edition, pages) and the departures.
What the extractor itself put under "outside" is counted, not flagged.

Identifiers are: gazette numbers (G.S.R. 205(E), S.O. 5458(E)), office memorandum
numbers (F.1/1/2021-PPD), rule, section and paragraph numbers, Japanese article
numbers (52条(1)(q)), law-report citations ((2012) 345 ITR 494), titles of rules,
acts and regulations with their year, and dates (24th March, 2021 = 24.03.2021 =
2021年3月24日). A paragraph number counts as shown when a quotation begins a
paragraph with it ("168. Given ...").

X2 says "not shown", not "wrong". Most of what it flags may be true, and some may
be printed in the source and simply not quoted. What it marks is a statement the
report asks the reader to take on trust.

Usage:
    python3 extractcheck.py REPORT.json [REPORT.json ...] [--source PAGES] [--json]

PAGES is the source text: pdftotext output (pages split by form feeds; the PDF
page is the position), or JSON {"pages": [{"pdf_page": 1, "printed_page": "24",
"text": "..."}]}, or the lines file written by pdflines.py. --source applies to a
single report.

Exit status: 0 no flags, 1 flags, 2 the input could not be read.
Standard library only. CC0 1.0. Part of the citation provenance kit (v1.9).
"""
import argparse
import json
import re
import sys
import unicodedata

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}
MONTH_RE = "(" + "|".join(m.capitalize() for m in MONTHS) + ")"

DATE_PATTERNS = [
    (re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+" + MONTH_RE + r",?\s+(\d{4})\b"), ("d", "m", "y")),
    (re.compile(r"\b" + MONTH_RE + r"\s+(\d{1,2}),?\s+(\d{4})\b"), ("m", "d", "y")),
    (re.compile(r"(?<![\d.])(\d{1,2})\.(\d{1,2})\.(\d{4})(?![\d.])"), ("d", "m", "y")),
    (re.compile(r"(?<![\d.])(\d{4})\.(\d{1,2})\.(\d{1,2})(?![\d.])"), ("y", "m", "d")),
    (re.compile(r"(?<!\d)(\d{4})-(\d{1,2})-(\d{1,2})(?!\d)"), ("y", "m", "d")),
    (re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日"), ("y", "m", "d")),
]

TITLE_WORD = r"(?:[A-Z][\w&'’-]*|\([A-Z][\w&'’ ,-]*\))"
PATTERNS = [
    ("gazette", re.compile(r"\b(G\.\s*S\.\s*R|S\.\s*O)\.?\s*(\d+)\s*\(\s*E\s*\)"),
     lambda m: "{}. {}(E)".format(re.sub(r"\s", "", m.group(1)), m.group(2))),
    ("memorandum", re.compile(r"\bF\.\s*/?\s*\d+(?:\s*/\s*\d+)*\s*/\s*\d{4}\s*-\s*PPD\b"),
     lambda m: re.sub(r"\s", "", m.group(0))),
    ("rule", re.compile(r"\b[Rr]ules?\s+(\d+[A-Z]?(?:\s*\(\s*[0-9A-Za-z]+\s*\))*)"),
     lambda m: "rule " + re.sub(r"\s", "", m.group(1)).lower()),
    ("section", re.compile(r"\b(?:[Ss]ections?|[Ss]ec\.|s\.)\s*(\d+[A-Z]?(?:\s*\(\s*[0-9A-Za-z]+\s*\))*)"),
     lambda m: "section " + re.sub(r"\s", "", m.group(1)).lower()),
    ("paragraph", re.compile(r"\b(?:paras?|paragraphs?|¶)\.?\s*(\d+(?:\.\d+)?)"),
     lambda m: "para " + m.group(1)),
    ("article", re.compile(r"(\d+)条((?:\d+項)?(?:\d+号)?(?:\s*[（(]\s*[0-9A-Za-z]+\s*[）)])*)"),
     lambda m: "art " + m.group(1) + re.sub(r"[\s（）()]", lambda c: {"（": "(", "）": ")", "(": "(", ")": ")"}.get(c.group(0), ""), m.group(2)).lower()),
    ("report", re.compile(r"\(\s*(\d{4})\s*\)\s*(\d+)\s+([A-Z]{2,5})(?:\s*\(\s*[A-Za-z]+\s*\))?\s+(\d+)"),
     lambda m: "({}) {} {} {}".format(m.group(1), m.group(2), m.group(3), m.group(4))),
    ("title", re.compile(r"(?<!\w)([A-Z][\w&'’-]*(?:\s+(?:" + TITLE_WORD + r"|of|and|for|the))*?\s+(?:Amendment\s+)?(?:Rules|Act|Regulations))\s*,?\s+(\d{4})\b"),
     lambda m: "{}, {}".format(LEADING.sub("", re.sub(r"\s+", " ", m.group(1))).lower(), m.group(2))),
]

LEADING = re.compile(r"^(?:(?:In|Under|The|the|Of|of|By|by|And|and|See|see|Vide|vide)\s+)+")
PARA_START = re.compile(r"(?:^|\n|(?<=\s))(\d{1,4})\.\s+(?=[A-Z“\"(])")


def normalise(text):
    """Fold full-width forms and collapse whitespace, for matching only."""
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("­", "").replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip()


def dates(text):
    found = set()
    for pat, order in DATE_PATTERNS:
        for m in pat.finditer(text):
            parts = dict(zip(order, m.groups()))
            month = parts["m"]
            month = MONTHS[month.lower()] if month.isalpha() else int(month)
            day, year = int(parts["d"]), int(parts["y"])
            if 1 <= month <= 12 and 1 <= day <= 31:
                found.add(("date", "{:04d}-{:02d}-{:02d}".format(year, month, day)))
    return found


def identifiers(text, verbatim=False):
    """Return {(kind, normal form)} for the identifiers in text."""
    text = normalise(text)
    found = dates(text)
    for kind, pat, norm in PATTERNS:
        for m in pat.finditer(text):
            found.add((kind, norm(m)))
    if verbatim:
        for m in PARA_START.finditer(text):
            found.add(("paragraph", "para " + m.group(1)))
    return found


def quote_texts(item):
    return [q.get("text", "") for q in item.get("quotes", []) + item.get("footnotes", [])]


def prose_fields(report):
    """Yield (where, text) for every field written in the extractor's own words."""
    for key in ("title", "issuer", "edition", "pages"):
        if report.get("source", {}).get(key):
            yield "source." + key, report["source"][key]
    for i, text in enumerate(report.get("remarks", []), 1):
        yield "report remark {}".format(i), text
    for item in report.get("items", []):
        for i, text in enumerate(item.get("remarks", []), 1):
            yield "item {} remark {}".format(item.get("n"), i), text
    for i, text in enumerate(report.get("departures", []), 1):
        yield "departure {}".format(i), text


def read_source(path):
    """Return [{"pdf_page": int, "printed_page": str|None, "text": str}]."""
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    if raw.lstrip().startswith("{"):
        data = json.loads(raw)
        pages = []
        for i, page in enumerate(data.get("pages", []), 1):
            if "lines" in page:
                text = "\n".join(line.get("text", "") for line in page["lines"])
            else:
                text = page.get("text", "")
            printed = page.get("printed_page")
            pages.append({"pdf_page": page.get("pdf_page", i),
                          "printed_page": None if printed is None else str(printed),
                          "text": text})
        return pages
    return [{"pdf_page": i, "printed_page": None, "text": t}
            for i, t in enumerate(raw.split("\f"), 1)]


def segments(quote):
    """The parts of a quotation to look for: an excerpt is split at […]."""
    parts = re.split(r"\s*\[(?:…|\.\.\.)\]\s*", quote.get("text", "")) if quote.get("excerpt") else [quote.get("text", "")]
    return [normalise(p) for p in parts if normalise(p)]


def page_matches(page, wanted):
    wanted = str(wanted).strip()
    return wanted in (str(page["pdf_page"]), page["printed_page"])


def page_list(text):
    """'34', '34〜35', '34-35', 'p.1–5' -> ['34', '35'] (endpoints and what lies between)."""
    nums = [int(n) for n in re.findall(r"\d+", str(text or ""))]
    if len(nums) == 2 and nums[0] < nums[1] <= nums[0] + 20:
        return [str(n) for n in range(nums[0], nums[1] + 1)]
    return [str(n) for n in nums]


def check(report, source=None):
    flags = []
    shown, given, declared = set(), set(), set()
    for item in report.get("items", []):
        given |= identifiers(item.get("target", ""))
        for text in quote_texts(item):
            shown |= identifiers(text, verbatim=True)
        for text in item.get("search_record", []):
            shown |= identifiers(text)
    for entry in report.get("outside", []):
        declared |= identifiers(entry.get("text", ""))
    in_source = set()
    if source:
        for page in source:
            in_source |= identifiers(page["text"], verbatim=True)

    counts = {"shown": 0, "given": 0, "in source": 0, "declared": 0, "not shown": 0}
    seen = set()
    for where, text in prose_fields(report):
        for ident in sorted(identifiers(text)):
            key = (where, ident)
            if key in seen:
                continue
            seen.add(key)
            if ident in shown:
                counts["shown"] += 1
            elif ident in given:
                counts["given"] += 1
            elif ident in in_source:
                counts["in source"] += 1
            elif ident in declared:
                counts["declared"] += 1
            else:
                counts["not shown"] += 1
                flags.append({"check": "X2", "where": where, "kind": ident[0], "identifier": ident[1],
                              "message": "{} {!r} is not shown by the report's verbatim text, given by the request{}, or declared as outside".format(
                                  ident[0], ident[1], ", found in the source" if source else "")})

    for item in report.get("items", []):
        n = item.get("n")
        if item.get("status") == "not_in_source" and not item.get("search_record"):
            flags.append({"check": "X3", "where": "item {}".format(n),
                          "message": "reported not in the source, with no search record"})
        if item.get("status") in ("found", "undeterminable") and not (item.get("page_pdf") or item.get("page_printed")):
            flags.append({"check": "X4", "where": "item {}".format(n), "message": "reported found, with no page"})
        if source:
            for qi, quote in enumerate(item.get("quotes", []) + item.get("footnotes", []), 1):
                wanted = quote.get("page_pdf") or item.get("page_pdf") or item.get("page_printed")
                pages = [p for p in source if any(page_matches(p, w) for w in page_list(wanted))]
                for seg in segments(quote):
                    if any(seg in normalise(p["text"]) for p in pages):
                        continue
                    elsewhere = [str(p["pdf_page"]) for p in source if seg in normalise(p["text"])]
                    flags.append({"check": "X1", "where": "item {} quote {}".format(n, qi),
                                  "message": "not on page {}{}".format(
                                      wanted or "(none given)",
                                      "; found on PDF page " + ", ".join(elsewhere) if elsewhere else "; not found in the source")})
    status = {"found": 0, "not_in_source": 0, "undeterminable": 0}
    for item in report.get("items", []):
        status[item.get("status")] = status.get(item.get("status"), 0) + 1
    return {"id": report.get("id"), "title": report.get("source", {}).get("title", ""),
            "items": len(report.get("items", [])), "status": status, "identifiers": counts, "flags": flags}


def load(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    reports = data if isinstance(data, list) else [data]
    for r in reports:
        if not isinstance(r, dict) or "items" not in r or "id" not in r:
            raise ValueError("{}: not an extraction report (needs id and items)".format(path))
        for item in r["items"]:
            if item.get("status") not in ("found", "not_in_source", "undeterminable"):
                raise ValueError("{}: item {}: unknown status {!r}".format(path, item.get("n"), item.get("status")))
    return reports


def render(result):
    s = result["status"]
    c = result["identifiers"]
    out = ["report {}  {}".format(result["id"], result["title"][:60]).rstrip(),
           "  items {}: found {} / not in source {} / undeterminable {}".format(
               result["items"], s["found"], s["not_in_source"], s["undeterminable"]),
           "  identifiers in the extractor's own words: shown {} / given {} / in source {} / declared {} / not shown {}".format(
               c["shown"], c["given"], c["in source"], c["declared"], c["not shown"])]
    for f in result["flags"]:
        if f["check"] == "X2":
            out.append("  X2 {}: {} {}".format(f["where"], f["kind"], f["identifier"]))
        else:
            out.append("  {} {}: {}".format(f["check"], f["where"], f["message"]))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("reports", nargs="+")
    ap.add_argument("--source", help="the source text (pdftotext output, pages JSON or pdflines JSON)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        reports = [r for path in args.reports for r in load(path)]
        source = read_source(args.source) if args.source else None
    except (OSError, ValueError) as e:
        print("extractcheck: {}".format(e), file=sys.stderr)
        return 2
    if source is not None and len(reports) != 1:
        print("extractcheck: --source applies to a single report", file=sys.stderr)
        return 2
    results = [check(r, source) for r in reports]
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("\n\n".join(render(r) for r in results))
    return 1 if any(r["flags"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
