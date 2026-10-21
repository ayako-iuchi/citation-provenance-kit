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
        verbatim text, not given by the request, not in the source text (with
        --source), not among what the extractor says it searched for, and not
        declared under "outside"
    X3  an item reported not in the source has no search record
    X4  an item reported found (or undeterminable) has no page, on the item or on
        every one of its quotations

Where each identifier stands:

    shown       in a quotation, a footnote, the cover and colophon as quoted, or
                a passage the search record quotes (inside 「」, “”, "" or ``)
    given       in an item as the request named it (not in what the requester
                expected; that is the "expected" field, and is not counted)
    in source   in the source text given with --source
    searched    elsewhere in the search record: what the extractor says it
                searched for or found by searching. This is still the
                extractor's own account, so it is listed, not passed silently.
    declared    under "outside", where the extractor itself put it
    not shown   none of these: flagged X2

"The extractor's own words" are the remarks (per item and for the report), the
description of the source (title, issuer, edition, pages) and the departures.

Identifiers: gazette numbers (G.S.R. 205(E), GSR 205(E), S.O. 5458(E)), file
numbers of office memoranda (F.1/1/2021-PPD, F. No. 1/1/2021-PPD); rule, section,
paragraph and article numbers, with lists and ranges expanded ("Rules 1, 2 and 17
to 21", "para 168–170") and "sub-rule (1) of rule 3" read as rule 3(1); Japanese
条 numbers (52条(1)(q), 第52条第1項, 3条の2), which match a section or an article
of the same number, since 条 translates either; law-report citations ((2012) 345
ITR 494, AIR 2021 SC 102, [2021] 125 taxmann.com 42); titles of rules, acts and
regulations with their year; and dates (24th March, 2021 = 24.03.2021 =
24-03-2021 = 2021年3月24日; "1st day of April, 2022"; Sept 2021 is not a date).
A provision counts as shown if a more specific one is (rule 3(1) shows rule 3). A
paragraph number counts as shown when a quotation begins a paragraph with it
("168. Given ..."). A title counts as shown when a shown title ends with it, or
it ends with a shown title, word for word. Identifiers are found next to any
character that is not a Latin letter or digit, including Japanese text.

X2 says "not shown", not "wrong". Most of what it flags may be true, and some may
be printed in the source and simply not quoted. What it marks is a statement the
report asks the reader to take on trust. Counts are of distinct identifiers per
report; the flags list each place one occurs.

Usage:
    python3 extractcheck.py REPORT.json [REPORT.json ...] [--json]
    python3 extractcheck.py REPORT.json --source PAGES [--report ID] [--first-pdf-page N]

PAGES is the source text, one of:
    pdftotext output, pages split by form feeds. The first page is PDF page
        --first-pdf-page (default 1: pdftotext run without -f).
    JSON {"pages": [{"pdf_page": 1, "printed_page": "24", "text": "..."}]}
    the lines file written by pdflines.py, which records printed pages only. Its
        pages get PDF page numbers only with --first-pdf-page.
A page given as page_pdf is matched only against PDF pages, and page_printed only
against printed pages. --source applies to one report; with a file of several,
name it with --report.

Exit status: 0 no flags, 1 flags, 2 the input could not be read.
Standard library only. CC0 1.0. Part of the citation provenance kit (v1.9).
"""
import argparse
import json
import re
import sys
import unicodedata

L = r"(?<![A-Za-z0-9])"   # left edge: not after a Latin letter or digit (Japanese text is fine)
R = r"(?![A-Za-z0-9])"    # right edge

MONTHS = {}
for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july",
                       "august", "september", "october", "november", "december"], 1):
    MONTHS[m] = i
    MONTHS[m[:3]] = i
MONTHS["sept"] = 9
MONTH_RE = "(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\.?"

DATE_PATTERNS = [
    (re.compile(L + r"(\d{1,2})(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?" + MONTH_RE + r",?\s*(\d{4})" + R, re.I), ("d", "m", "y")),
    (re.compile(L + MONTH_RE + r"\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})" + R, re.I), ("m", "d", "y")),
    (re.compile(r"(?<![\d.\-/])(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})(?![\d.\-/])"), ("d", "m", "y")),
    (re.compile(r"(?<![\d.\-/])(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})(?![\d\-/]|\.\d)"), ("y", "m", "d")),
    (re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日"), ("y", "m", "d")),
]

PROVISION_TAIL = r"\d+[A-Z]?(?:\s*\(\s*[0-9A-Za-z]+\s*\))*"
LIST_TAIL = r"(?:\s*(?:,|and|&|to|[-–—~〜])\s*" + PROVISION_TAIL + r")*"
TITLE_KEY = r"(?:Rules|RULES|Act|ACT|Regulations|REGULATIONS)"
TITLE_WORD = r"(?:[A-Z][A-Za-z&'’.\-]*|\([A-Z][A-Za-z&'’ ,.\-]*\))"
TITLE_RE = re.compile(
    L + r"(" + TITLE_WORD + r"(?:\s+(?:" + TITLE_WORD + r"|(?:of|and|for|on)(?=\s+[A-Z(])))*?\s+(?:Amendment\s+|AMENDMENT\s+)?" + TITLE_KEY + r")"
    + r"\s*,?\s*(\d{4})" + R)
LEADING = re.compile(r"^(?:(?:In|IN|Under|UNDER|The|THE|Of|OF|By|BY|And|AND|See|SEE|Vide|VIDE|With|WITH)\s+)+")

PARA_START = re.compile(r"(?:^|(?<=\s))(\d{1,4})\.\s+(?=[A-Z“\"(])")
PARA_START_NOT_AFTER = re.compile(r"(?:[Rr]ules?|[Ss]ections?|[Pp]aras?|[Pp]aragraphs?|[Aa]rticles?|No|Nos|p|pp)\.?\s*$")

QUOTED = re.compile(r"「([^」]*)」|“([^”]*)”|\"([^\"]*)\"|`([^`]*)`|‘([^’]*)’")


def normalise(text, soft=False):
    """Fold full-width forms, quotes and dashes, and collapse whitespace, for matching only."""
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("­", "")
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"')):
        text = text.replace(a, b)
    if soft:
        text = re.sub(r"(?<=[a-z])-\s*\n\s*(?=[a-z])", "", text)
    return re.sub(r"\s+", " ", text).strip()


def expand_numbers(tail):
    """'1, 2 and 17 to 21' -> ['1', '2', '17', ..., '21']; '3(1)' -> ['3(1)']."""
    tail = re.sub(r"\s+", "", tail)
    parts = re.split(r",|and|&", tail)
    out = []
    for part in parts:
        if not part:
            continue
        m = re.fullmatch(r"(\d+)(?:to|[-–—~〜])(\d+)", part)
        if m and int(m.group(1)) < int(m.group(2)) <= int(m.group(1)) + 50:
            out += [str(n) for n in range(int(m.group(1)), int(m.group(2)) + 1)]
        else:
            out.append(part.lower())
    return out


def dates(text):
    found = set()
    for pat, order in DATE_PATTERNS:
        for m in pat.finditer(text):
            parts = dict(zip(order, m.groups()))
            month = parts["m"]
            month = MONTHS.get(month.lower().rstrip(".")) if not month.isdigit() else int(month)
            if month is None:
                continue
            day, year = int(parts["d"]), int(parts["y"])
            if 1 <= month <= 12 and 1 <= day <= 31 and 1800 <= year <= 2200:
                found.add(("date", "{:04d}-{:02d}-{:02d}".format(year, month, day)))
    return found


def jo(m):
    """Japanese 条: 52条(1)(q), 第52条第1項第2号, 3条の2."""
    num = m.group(1) + ("-" + m.group(2) if m.group(2) else "")
    tail = ""
    if m.group(3):
        tail += "(" + m.group(3) + ")"
    if m.group(4):
        tail += "(" + m.group(4) + ")"
    for x in re.findall(r"[（(]\s*([0-9A-Za-z]+)\s*[）)]", m.group(5) or ""):
        tail += "(" + x.lower() + ")"
    return ("条", num + tail)


PATTERNS = [
    ("gazette", re.compile(L + r"(G\.?\s*S\.?\s*R|S\.?\s*O)\.?\s*(\d+)\s*\(\s*E\s*\)"),
     lambda m: ["{}. {}(E)".format({"GSR": "G.S.R", "SO": "S.O"}[re.sub(r"[\s.]", "", m.group(1))], m.group(2))]),
    ("file number", re.compile(L + r"F\s*\.?\s*(?:No\s*\.?\s*)?(/?\s*[A-Z]*-?\d+(?:\s*/\s*\d+)*\s*/\s*\d{4})\s*[-–—]\s*([A-Za-z&]+)" + R),
     lambda m: ["F." + re.sub(r"\s", "", m.group(1)) + "-" + m.group(2)]),
    ("rule", re.compile(r"(?<![A-Za-z0-9\-])[Rr]ules?\s+(?!\d{4}" + R + r")(" + PROVISION_TAIL + LIST_TAIL + r")"),
     lambda m: ["rule " + n for n in expand_numbers(m.group(1))]),
    ("rule", re.compile(L + r"sub-rule\s*\(\s*(\w+)\s*\)\s*of\s+rule\s+(\d+[A-Z]?)" + R, re.I),
     lambda m: ["rule {}({})".format(m.group(2).lower(), m.group(1).lower())]),
    ("section", re.compile(L + r"(?:[Ss]ections?|SECTIONS?|[Ss]ec\.|[Ss]s?\.|u/s)\s*(?!\d{4}" + R + r")(" + PROVISION_TAIL + LIST_TAIL + r")(?!\s*[—–-]\s*[Ss]ub)"),
     lambda m: ["section " + n for n in expand_numbers(m.group(1))]),
    ("article", re.compile(L + r"(?:[Aa]rticles?|ARTICLES?|[Aa]rt\.)\s*(" + PROVISION_TAIL + LIST_TAIL + r")"),
     lambda m: ["article " + n for n in expand_numbers(m.group(1))]),
    ("paragraph", re.compile(r"(?:" + L + r"(?:[Pp]aras?|PARAS?|[Pp]aragraphs?|PARAGRAPHS?)\.?\s*|¶\s*)(\d+(?:\.\d+)?" + LIST_TAIL.replace(PROVISION_TAIL, r"\d+(?:\.\d+)?") + r")"),
     lambda m: ["para " + n for n in expand_numbers(m.group(1))]),
    ("report", re.compile(r"[\[(]\s*(\d{4})\s*[\])]\s*(\d+)\s+([A-Z](?:\.?[A-Za-z]){1,8}\.?(?:\.com)?)(?:\s*\(\s*[A-Za-z]+\s*\))?\s+(\d+)" + R),
     lambda m: ["({}) {} {} {}".format(m.group(1), m.group(2), m.group(3).replace(".", "").upper() if not m.group(3).lower().endswith("com") else m.group(3).lower(), m.group(4))]),
    ("report", re.compile(r"\[\s*(\d{4})\s*\]\s*(\d+)\s+taxmann\.com\s+(\d+)" + R, re.I),
     lambda m: ["[{}] {} taxmann.com {}".format(m.group(1), m.group(2), m.group(3))]),
    ("report", re.compile(L + r"(AIR(?:ONLINE)?)\s+(\d{4})\s+([A-Z]{2,4})\s+(\d+)" + R),
     lambda m: ["{} {} {} {}".format(m.group(1), m.group(2), m.group(3), m.group(4))]),
]
JO_RE = re.compile(r"(?<![0-9])第?(\d+)条(?!件)(?:の(\d+))?(?:第?(\d+)項)?(?:第?(\d+)号)?((?:\s*[（(]\s*[0-9A-Za-z]+\s*[）)])*)")


def titles(text):
    out = set()
    for m in TITLE_RE.finditer(text):
        name = LEADING.sub("", re.sub(r"\s+", " ", m.group(1)))
        out.add(("title", "{}, {}".format(name.lower(), m.group(2))))
    return out


def identifiers(text, verbatim=False):
    """Return {(kind, normal form)} for the identifiers in text."""
    text = normalise(text)
    found = dates(text) | titles(text)
    for kind, pat, norm in PATTERNS:
        for m in pat.finditer(text):
            for value in norm(m):
                found.add((kind, value))
    for m in JO_RE.finditer(text):
        found.add(jo(m))
    if verbatim:
        for m in PARA_START.finditer(text):
            if not PARA_START_NOT_AFTER.search(text[:m.start()]):
                found.add(("paragraph", "para " + m.group(1)))
    return found


PROVISION_KINDS = {"rule", "section", "article", "paragraph", "条"}


def provision_parts(ident):
    kind, value = ident
    num = value.split(" ", 1)[1] if kind != "条" else value
    return kind, num


def covered(ident, pool):
    """Is ident in pool, allowing a more specific provision, a 条 for a section or
    article of the same number, and a title that ends with the other word for word?"""
    if ident in pool:
        return True
    kind, value = ident
    if kind == "title":
        name, year = value.rsplit(", ", 1)
        for k, v in pool:
            if k != "title":
                continue
            n2, y2 = v.rsplit(", ", 1)
            if y2 == year and (n2 == name or n2.endswith(" " + name) or name.endswith(" " + n2)):
                return True
        return False
    if kind in PROVISION_KINDS:
        if kind in ("rule", "paragraph"):
            kinds = {kind}
        elif kind == "条":
            kinds = {"section", "article", "条"}
        else:
            kinds = {kind, "条"}
        _, num = provision_parts(ident)
        for other in pool:
            if other[0] not in kinds:
                continue
            _, onum = provision_parts(other)
            if onum == num or onum.startswith(num + "("):
                return True
    return False


ALLOWED = {
    "report": {"id", "date", "prompt", "transcribed", "source", "items", "remarks", "outside", "departures"},
    "source": {"title", "issuer", "edition", "pages", "file", "cover"},
    "item": {"n", "target", "expected", "status", "page_pdf", "page_printed", "quotes", "footnotes", "search_record", "remarks"},
    "quote": {"text", "page_pdf", "page_printed", "excerpt"},
    "outside": {"text", "origin"},
}
STATUSES = ("found", "not_in_source", "undeterminable")


def validate(r, where):
    def fail(msg):
        raise ValueError("{}: {}".format(where, msg))

    def strings(obj, key, ctx):
        v = obj.get(key, [])
        if not isinstance(v, list) or not all(isinstance(s, str) for s in v):
            fail("{}{} must be a list of strings".format(ctx, key))

    def quotes(obj, key, ctx):
        v = obj.get(key, [])
        if not isinstance(v, list):
            fail("{}{} must be a list".format(ctx, key))
        for q in v:
            if not isinstance(q, dict) or not isinstance(q.get("text"), str):
                fail("{}{}: each entry needs a text".format(ctx, key))
            extra = set(q) - ALLOWED["quote"]
            if extra:
                fail("{}{}: unknown field(s) {}".format(ctx, key, ", ".join(sorted(extra))))

    if not isinstance(r, dict):
        fail("a report must be a JSON object")
    for key in ("id", "source", "items"):
        if key not in r:
            fail("missing {}".format(key))
    extra = set(r) - ALLOWED["report"]
    if extra:
        fail("unknown field(s) {}".format(", ".join(sorted(extra))))
    if not isinstance(r["source"], dict):
        fail("source must be an object")
    extra = set(r["source"]) - ALLOWED["source"]
    if extra:
        fail("source: unknown field(s) {}".format(", ".join(sorted(extra))))
    for key in ("title", "issuer", "edition", "pages", "file"):
        if key in r["source"] and not isinstance(r["source"][key], str):
            fail("source.{} must be a string".format(key))
    quotes(r["source"], "cover", "source.")
    strings(r, "remarks", "")
    strings(r, "departures", "")
    if not isinstance(r.get("outside", []), list) or not all(
            isinstance(o, dict) and isinstance(o.get("text"), str) and isinstance(o.get("origin"), str)
            and not set(o) - ALLOWED["outside"] for o in r.get("outside", [])):
        fail("outside: each entry needs text and origin, and nothing else")
    if not isinstance(r["items"], list):
        fail("items must be a list")
    for item in r["items"]:
        if not isinstance(item, dict):
            fail("each item must be an object")
        ctx = "item {}: ".format(item.get("n"))
        extra = set(item) - ALLOWED["item"]
        if extra:
            fail(ctx + "unknown field(s) {}".format(", ".join(sorted(extra))))
        if not isinstance(item.get("n"), int) or not isinstance(item.get("target"), str):
            fail(ctx + "needs a whole-number n and a target")
        if item.get("status") not in STATUSES:
            fail(ctx + "unknown status {!r}".format(item.get("status")))
        for key in ("page_pdf", "page_printed", "expected"):
            if key in item and not isinstance(item[key], str):
                fail(ctx + "{} must be a string".format(key))
        quotes(item, "quotes", ctx)
        quotes(item, "footnotes", ctx)
        strings(item, "search_record", ctx)
        strings(item, "remarks", ctx)


def prose_fields(report):
    """Yield (where, text) for every field written in the extractor's own words."""
    for key in ("title", "issuer", "edition", "pages"):
        if report["source"].get(key):
            yield "source." + key, report["source"][key]
    for i, text in enumerate(report.get("remarks", []), 1):
        yield "report remark {}".format(i), text
    for item in report["items"]:
        for i, text in enumerate(item.get("remarks", []), 1):
            yield "item {} remark {}".format(item["n"], i), text
    for i, text in enumerate(report.get("departures", []), 1):
        yield "departure {}".format(i), text


def read_source(path, first_pdf_page=None):
    """Return [{"pdf_page": int|None, "printed_page": str|None, "text": str}]."""
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    stripped = raw.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        data = json.loads(raw)
        if not isinstance(data, dict) or not isinstance(data.get("pages"), list):
            raise ValueError("{}: a JSON source must be an object with a list of pages".format(path))
        pages = []
        for i, page in enumerate(data["pages"]):
            if not isinstance(page, dict):
                raise ValueError("{}: each page must be an object".format(path))
            if "lines" in page:
                text = "\n".join(line.get("text", "") for line in page["lines"] if isinstance(line, dict))
            else:
                text = page.get("text", "")
            pdf = page.get("pdf_page")
            if pdf is None and first_pdf_page is not None:
                pdf = first_pdf_page + i
            printed = page.get("printed_page")
            pages.append({"pdf_page": pdf, "printed_page": None if printed is None else str(printed), "text": text})
        return pages
    start = 1 if first_pdf_page is None else first_pdf_page
    return [{"pdf_page": start + i, "printed_page": None, "text": t}
            for i, t in enumerate(raw.split("\f"))]


def segments(quote):
    """The parts of a quotation to look for: an excerpt is split where it was shortened."""
    text = quote.get("text", "")
    if quote.get("excerpt"):
        parts = re.split(r"\s*(?:\[\s*(?:…|\.\.\.)\s*\]|…|\.\.\.)\s*", text)
    else:
        parts = [text]
    return [p for p in (normalise(x) for x in parts) if p]


def page_list(text):
    """'34', '34〜35', '1–5, 115' -> ['34'], ['34', '35'], ['1', ..., '5', '115']."""
    out = []
    for part in re.split(r"[,、，]", unicodedata.normalize("NFKC", str(text or ""))):
        nums = [int(n) for n in re.findall(r"\d+", part)]
        if len(nums) == 2 and nums[0] < nums[1] <= nums[0] + 50:
            out += [str(n) for n in range(nums[0], nums[1] + 1)]
        else:
            out += [str(n) for n in nums]
        romans = re.findall(r"\b([ivxlcdm]+)\b", part.lower())
        out += romans
    return out


def wanted_pages(source, quote, item):
    """The pages a quotation should be on, and how they were named."""
    for field, key in (("page_pdf", "pdf_page"), ("page_printed", "printed_page")):
        given = quote.get(field)
        if given:
            return field, given, [p for p in source if p[key] is not None and str(p[key]) in page_list(given)]
    for field, key in (("page_pdf", "pdf_page"), ("page_printed", "printed_page")):
        given = item.get(field)
        if given:
            return field, given, [p for p in source if p[key] is not None and str(p[key]) in page_list(given)]
    return None, None, []


def on_pages(seg, pages):
    texts = [normalise(p["text"]) for p in pages] + [normalise(p["text"], soft=True) for p in pages]
    if any(seg in t for t in texts):
        return True
    if len(pages) > 1:
        joined = " ".join(normalise(p["text"]) for p in pages)
        joined_soft = normalise("\n".join(p["text"] for p in pages), soft=True)
        return seg in joined or seg in joined_soft
    return False


def check(report, source=None):
    flags = []
    shown, given, declared, searched = set(), set(), set(), set()
    for q in report["source"].get("cover", []):
        shown |= identifiers(q.get("text", ""), verbatim=True)
    for item in report["items"]:
        given |= identifiers(item.get("target", ""))
        for q in item.get("quotes", []) + item.get("footnotes", []):
            shown |= identifiers(q.get("text", ""), verbatim=True)
        for text in item.get("search_record", []):
            inside = [g for m in QUOTED.finditer(text) for g in m.groups() if g]
            for part in inside:
                shown |= identifiers(part, verbatim=True)
            searched |= identifiers(QUOTED.sub(" ", text))
    for entry in report.get("outside", []):
        declared |= identifiers(entry.get("text", ""))
    in_source = set()
    if source:
        for page in source:
            in_source |= identifiers(page["text"], verbatim=True)

    places = {}
    for where, text in prose_fields(report):
        for ident in sorted(identifiers(text)):
            places.setdefault(ident, [])
            if where not in places[ident]:
                places[ident].append(where)
    counts = {"shown": 0, "given": 0, "in source": 0, "searched": 0, "declared": 0, "not shown": 0}
    searched_only = []
    for ident in sorted(places):
        if covered(ident, shown):
            counts["shown"] += 1
        elif covered(ident, given):
            counts["given"] += 1
        elif covered(ident, in_source):
            counts["in source"] += 1
        elif covered(ident, searched):
            counts["searched"] += 1
            searched_only.append({"kind": ident[0], "identifier": ident[1], "where": places[ident]})
        elif covered(ident, declared):
            counts["declared"] += 1
        else:
            counts["not shown"] += 1
            for where in places[ident]:
                flags.append({"check": "X2", "where": where, "kind": ident[0], "identifier": ident[1],
                              "message": "{} {!r} is not shown by the report's verbatim text, given by the request{}, searched for, or declared as outside".format(
                                  ident[0], ident[1], ", found in the source" if source else "")})

    for item in report["items"]:
        n = item["n"]
        all_quotes = item.get("quotes", []) + item.get("footnotes", [])
        if item["status"] == "not_in_source" and not item.get("search_record"):
            flags.append({"check": "X3", "where": "item {}".format(n),
                          "message": "reported not in the source, with no search record"})
        if item["status"] in ("found", "undeterminable") and not (item.get("page_pdf") or item.get("page_printed")):
            if not all_quotes or not all(q.get("page_pdf") or q.get("page_printed") for q in all_quotes):
                flags.append({"check": "X4", "where": "item {}".format(n),
                              "message": "reported {} with no page".format(item["status"].replace("_", " "))})
        if source:
            for qi, quote in enumerate(all_quotes, 1):
                field, wanted, pages = wanted_pages(source, quote, item)
                for seg in segments(quote):
                    if pages and on_pages(seg, pages):
                        continue
                    elsewhere = [p for p in source if on_pages(seg, [p])]
                    where_found = ", ".join("PDF page {}".format(p["pdf_page"]) if p["pdf_page"] is not None
                                            else "printed page {}".format(p["printed_page"]) for p in elsewhere)
                    if wanted and not pages:
                        what = "{} {} is not in the source as given".format(field.replace("_", " "), wanted)
                    else:
                        what = "not on {} {}".format(field.replace("_", " ") if field else "page", wanted or "(none given)")
                    flags.append({"check": "X1", "where": "item {} quote {}".format(n, qi),
                                  "message": what + ("; found on " + where_found if where_found else "; not found in the source")})
    status = {s: 0 for s in STATUSES}
    for item in report["items"]:
        status[item["status"]] += 1
    return {"id": report["id"], "title": report["source"].get("title", ""),
            "items": len(report["items"]), "status": status, "identifiers": counts,
            "searched_only": searched_only, "flags": flags}


def load(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    reports = data if isinstance(data, list) else [data]
    for i, r in enumerate(reports, 1):
        validate(r, "{} report {}".format(path, i) if len(reports) > 1 else path)
    return reports


def render(result):
    s = result["status"]
    c = result["identifiers"]
    out = ["report {}  {}".format(result["id"], result["title"][:60]).rstrip(),
           "  items {}: found {} / not in source {} / undeterminable {}".format(
               result["items"], s["found"], s["not_in_source"], s["undeterminable"]),
           "  identifiers in the extractor's own words: shown {} / given {} / in source {} / searched {} / declared {} / not shown {}".format(
               c["shown"], c["given"], c["in source"], c["searched"], c["declared"], c["not shown"])]
    for f in result["flags"]:
        if f["check"] == "X2":
            out.append("  X2 {}: {} {}".format(f["where"], f["kind"], f["identifier"]))
        else:
            out.append("  {} {}: {}".format(f["check"], f["where"], f["message"]))
    for s in result["searched_only"]:
        out.append("  (searched only) {}: {} {}".format(", ".join(s["where"]), s["kind"], s["identifier"]))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("reports", nargs="+")
    ap.add_argument("--source", help="the source text (pdftotext output, pages JSON or pdflines JSON)")
    ap.add_argument("--report", help="with --source: the id of the report to check, when a file holds several")
    ap.add_argument("--first-pdf-page", type=int, help="the PDF page number of the first page in --source")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        reports = [r for path in args.reports for r in load(path)]
        source = read_source(args.source, args.first_pdf_page) if args.source else None
    except (OSError, ValueError) as e:
        print("extractcheck: {}".format(e), file=sys.stderr)
        return 2
    if args.report:
        reports = [r for r in reports if r["id"] == args.report]
        if not reports:
            print("extractcheck: no report with id {!r}".format(args.report), file=sys.stderr)
            return 2
    if source is not None and len(reports) != 1:
        print("extractcheck: --source applies to a single report; name it with --report", file=sys.stderr)
        return 2
    results = [check(r, source) for r in reports]
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("\n\n".join(render(r) for r in results))
    return 1 if any(r["flags"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
