#!/usr/bin/env python3
"""citelint — mechanical checks for a document that uses component-graded citation.

A written rule does not fire on its own. These checks do. They cover only what a
machine can see in the text itself; they do not read sources, and they cannot
tell whether a reading is correct or whether a cited provision is still in force.

Usage:
    python3 citelint.py DOCUMENT [--format markdown|rendered] [--lang en|ja] [--json]

    markdown  the author's source (Markdown table separators are legitimate)
    rendered  text taken from the published file, e.g. extracted from the PDF
              (anything that looks like markup is a leak)

Exit status is 1 if anything is reported, so it can run in CI.

Checks
    C1 undefined-token   a log reference (#N, X-NN) that no log entry defines
    C2 count-above       "the six above" when the section has a different number of
                         preceding subsections
    C3 drafting-note     leftover notes to self ("should be amended accordingly", TODO, [LINK])
    C4 contents-heading  an entry in the Contents with no matching heading in the body
    C5 notation          a [component: grade] slot whose component is outside the
                         closed vocabulary, or whose grade is not A-D or an em dash
    C6 markup-leak       markup printed as text: &nbsp;, backticks, table-alignment rows,
                         empty table rows (rendered format only for the last three)

CC0 1.0. Part of the citation provenance kit.
"""
import argparse
import json
import re
import sys
import unicodedata

COMPONENTS = {
    "en": {"wording", "figure", "page", "date", "edition", "identifier", "existence",
           "commencement", "attribution", "dependency"},
    # §4-2 of the Japanese edition declares each component as a pair, e.g. wording（語）
    "ja": {"語", "数値", "頁", "日付", "版", "識別子", "存在", "施行", "帰属", "依存",
           "wording", "figure", "page", "date", "edition", "identifier", "existence",
           "commencement", "attribution", "dependency"},
}
NUM_EN = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve".split())}
NUM_JA = {c: i for i, c in enumerate("〇一二三四五六七八九", 0)}
DRAFT_PATTERNS = [
    r"\bshould be (?:amended|updated|revised|changed) accordingly\b",
    r"\bTODO\b", r"\bTBD\b", r"\bFIXME\b", r"\bXXX\b",
    r"[\[［]\s*[^\]］]{0,20}LINK\s*[\]］]",
    r"に合わせて改める",
]


class Finding:
    def __init__(self, check, line, text, detail):
        self.check, self.line, self.text, self.detail = check, line, text.strip(), detail

    def as_dict(self):
        return {"check": self.check, "line": self.line, "detail": self.detail, "text": self.text[:160]}


QUOTED = re.compile(r"“[^”]*”|\"[^\"]*\"|「[^」]*」|『[^』]*』")


def unquoted(line, fmt="rendered"):
    """The line with quoted material removed: a quotation of a defect is not the defect."""
    line = QUOTED.sub(" ", line)
    if fmt == "markdown":
        line = re.sub(r"`[^`]*`", " ", line)
    return line


def norm_heading(s):
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"^(?:\d+\.|[A-Z]-\d+|\d+-\d+)\s*", "", s.strip())
    s = re.sub(r"[\s*_`]+", " ", s)
    return s.strip().lower()


def table_cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_align_row(cells):
    return bool(cells) and all(re.fullmatch(r":?-{1,}:?", c) for c in cells if c) and any(cells)


# ---------------------------------------------------------------- checks

def c1_undefined_tokens(lines):
    """Log entries are the first cell of rows in a table whose header starts with '#'."""
    defined, in_log = set(), False
    for ln in lines:
        if ln.strip().startswith("|"):
            cells = table_cells(ln)
            if cells and cells[0] == "#":
                in_log = True
                continue
            m0 = re.match(r"(\d+|X-\d+)(?![\d-])", cells[0]) if cells else None
            if in_log and m0:
                defined.add(m0.group(1))
        elif not ln.strip() or ln.startswith("#"):
            in_log = False
        m = re.match(r"^\W*(X-\d{2})(?:\W*(?:and|と|・|、)\W*(X-\d{2}))?\W*(?:are|is|は|：)", ln)
        if m:
            defined.update(t for t in m.groups() if t)
    out = []
    for i, ln in enumerate(lines, 1):
        if ln.strip().startswith("|") and re.match(r"(\d+|X-\d+)(?![\d-])", table_cells(ln)[0] or "-") and re.match(r"(\d+|X-\d+)(?![\d-])", table_cells(ln)[0]).group(1) in defined:
            continue
        for tok in re.findall(r"(?<![\w-])X-\d{2}\b", unquoted(ln)):
            if tok not in defined:
                out.append(Finding("C1", i, ln, f"log token {tok} is used but no log entry defines it"))
        if re.search(r"(?:→|Log references|参照)", ln):
            for n in re.findall(r"#(\d{1,3})\b", ln):
                if defined and n not in defined:
                    out.append(Finding("C1", i, ln, f"log entry #{n} is referenced but not in the log"))
    return out


def c2_count_above(lines, lang):
    out, siblings, current_top = [], [], None
    head = re.compile(r"^(#{2,3})\s+(\d+)-(\d+)\b" if lang == "en" else r"^(#{2,3})\s+(\d+)-(\d+)")
    for i, ln in enumerate(lines, 1):
        m = head.match(ln)
        if m:
            top = m.group(2)
            if top != current_top:
                current_top, siblings = top, []
            siblings.append(m.group(3))
            continue
        if ln.startswith("## "):
            current_top, siblings = None, []
            continue
        if not siblings:
            continue
        preceding = len(siblings) - 1
        if lang == "en":
            for w in re.findall(r"\bthe (\w+) above\b", ln, flags=re.I):
                n = NUM_EN.get(w.lower())
                if n is not None and n != preceding:
                    out.append(Finding("C2", i, ln, f'"the {w} above", but {preceding} subsections precede this one'))
        else:
            for w in re.findall(r"上(?:記|の|記の)([0-9０-９一二三四五六七八九]+)つ", ln):
                w2 = unicodedata.normalize("NFKC", w)
                n = int(w2) if w2.isdigit() else NUM_JA.get(w2)
                if n is not None and n != preceding:
                    out.append(Finding("C2", i, ln, f"「上記{w}つ」だが、この節の前に小節が{preceding}つある"))
    return out


def c3_drafting_notes(lines):
    out = []
    for i, ln in enumerate(lines, 1):
        for p in DRAFT_PATTERNS:
            m = re.search(p, unquoted(ln))
            if m:
                out.append(Finding("C3", i, ln, f'drafting note left in the text: "{m.group(0)}"'))
    return out


def c4_contents_vs_headings(lines):
    start = None
    for i, ln in enumerate(lines):
        if re.match(r"^#{2,3}\s+(Contents|目次)\s*$", ln.strip()):
            start = i
            break
    if start is None:
        return []
    entries, end = [], len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("#"):
            end = j
            break
        t = re.sub(r"^\s*[-*]\s*", "", lines[j]).replace("&nbsp;", " ")
        for part in re.split(r"\s{3,}", t):
            if part.strip():
                entries.append((j + 1, part.strip()))
    headings = {norm_heading(re.sub(r"^#+\s*", "", ln)) for ln in lines[end:] if ln.startswith("#")}
    out = []
    for lineno, e in entries:
        if norm_heading(e) not in headings:
            out.append(Finding("C4", lineno, e, "listed in the Contents, but no heading with this text exists in the body"))
    return out


def c5_notation(lines, lang):
    vocab = COMPONENTS[lang]
    out = []
    slot = re.compile(r"[\[［]\s*([^\]］|｜]+?)\s*[:：]\s*([^\]］|｜]*?)\s*(?=[|｜\]］])")
    for i, ln in enumerate(lines, 1):
        for block in re.findall(r"[\[［][^\]］]*[:：][^\]］]*[\]］]", ln):
            body = block[1:-1]
            for part in re.split(r"[|｜]", body):
                if ":" not in part and "：" not in part:
                    break
                comp, grade = re.split(r"[:：]", part, maxsplit=1)
                comp = re.sub(r"[*_`]", "", comp).strip()
                grade = re.sub(r"[*_`]", "", grade).strip()
                if lang == "en" and not re.fullmatch(r"[a-z ]+", comp):
                    break  # not a notation slot (e.g. a quoted bracket)
                if comp not in vocab and comp not in {"component", "成分"}:
                    out.append(Finding("C5", i, ln, f'component "{comp}" is not in the closed vocabulary'))
                g = grade.split()[0] if grade else ""
                if g and g not in {"A", "B", "C", "D", "—", "grade", "級"} and not re.fullmatch(r"[A-D](?:\s.*)?", grade):
                    out.append(Finding("C5", i, ln, f'grade "{grade}" is not A–D or an em dash'))
    return out


def c6_markup_leak(lines, fmt):
    out = []
    prev_header = False
    for i, ln in enumerate(lines, 1):
        if fmt == "rendered" and "&nbsp;" in unquoted(ln):
            out.append(Finding("C6", i, ln, "HTML entity &nbsp; printed as text"))
        if fmt == "rendered":
            n = unquoted(ln).count("`")
            if n:
                out.append(Finding("C6", i, ln, f"backtick printed as text ({n})"))
            if ln.strip().startswith("|"):
                cells = table_cells(ln)
                if is_align_row(cells):
                    out.append(Finding("C6", i, ln, "table-alignment row (:-: / ---) printed as a table row"))
                elif cells and all(c == "" for c in cells):
                    out.append(Finding("C6", i, ln, "empty table row"))
    return out


def lint(text, fmt="markdown", lang="en"):
    lines = text.splitlines()
    findings = []
    findings += c1_undefined_tokens(lines)
    findings += c2_count_above(lines, lang)
    findings += c3_drafting_notes(lines)
    findings += c4_contents_vs_headings(lines)
    findings += c5_notation(lines, lang)
    findings += c6_markup_leak(lines, fmt)
    return sorted(findings, key=lambda f: (f.line, f.check))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("document")
    ap.add_argument("--format", choices=["markdown", "rendered"], default="markdown")
    ap.add_argument("--lang", choices=["en", "ja"], default="en")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    fs = lint(open(a.document, encoding="utf-8").read(), a.format, a.lang)
    if a.json:
        print(json.dumps([f.as_dict() for f in fs], ensure_ascii=False, indent=1))
    else:
        for f in fs:
            print(f"{a.document}:{f.line}: {f.check} {f.detail}")
        counts = {}
        for f in fs:
            counts[f.check] = counts.get(f.check, 0) + 1
        print(f"{len(fs)} finding(s)" + (": " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) if fs else ""))
    return 1 if fs else 0


if __name__ == "__main__":
    sys.exit(main())
