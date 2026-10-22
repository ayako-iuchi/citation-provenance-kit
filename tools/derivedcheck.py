#!/usr/bin/env python3
"""derivedcheck — derived documents, and the version of the source each was made from.

A summary, a slide, a README or a citation file copies facts about another
document: its list of items, its count, its version, the date it was issued.
When the source moves, the copy becomes wrong without a word of it changing.
This tool keeps the copy tied to the version it was made from, and compares.

Three checks:

  1. The register of derived documents (register/derived.jsonl), against the
     status log's current edition of each source:

         python3 derivedcheck.py --log register/derived.jsonl \\
             --status register/status_log.jsonl --on 2026-10-22

     Each derived document gets one verdict for each source it was made from:
         current          made from the edition the status log gives today
         stale            made from another edition
         source-unknown   the status log has no edition for this source
         source-expired   the status log's edition has expired
     and these flags:
         not-in-document  the derived document does not itself say which
                          edition it was made from
         claimed-before-observed
                          another document said it was issued before anyone
                          had seen it (the record ran ahead of the fact)
         unobserved       it is said to be issued and has never been seen
     It does not say what in a stale document is wrong. That is a reading.

  2. The version labels a kit tree gives itself (--tree), which must agree:
     CITATION.cff, both READMEs, CHANGELOG, the workbook's Start here sheet and
     build_kit.py. It also lists the edition of the paper each place names.

         python3 derivedcheck.py --tree .
         python3 derivedcheck.py --tree . --ref v1.2      # a tag, via git

  3. The tags the README says exist, against a list of tags you give
     (--tags), for example from `git ls-remote --tags origin`.

Exit status: 0 nothing to report; 1 something reported; 2 a file could not be
read or a record is malformed. Standard library only. CC0 1.0. Part of the
citation provenance kit (kit v1.10).
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import zipfile
from io import BytesIO
from xml.etree import ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statuslog  # noqa: E402

VERSION_RE = re.compile(r"(?<![\w.])(?:[vV](\d+(?:\.\d+)*)|(\d+(?:\.\d+)+))(?![\w.]*\d)")
RECORD_KEYS = {"id", "derived", "from", "copies", "issued_on", "claimed", "observed",
               "recorded_on", "recorded_by", "supersedes", "note"}
REQUIRED = {"id", "derived", "from", "recorded_on", "recorded_by"}


class Malformed(Exception):
    pass


def version_of(text):
    """The first version number in a text, without a leading v: 'v1.1 (26 July)' -> '1.1'.

    A number without a dot counts only after a v ('v2'), so dates are not read as versions.
    """
    if text is None:
        return None
    m = VERSION_RE.search(str(text))
    return (m.group(1) or m.group(2)) if m else None


# --- 1. the register of derived documents --------------------------------------

def load(path):
    """Read derived.jsonl. Blank lines are ignored. Raises Malformed with the line number."""
    out = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError as e:
                raise Malformed(f"line {n}: not JSON ({e.msg})")
            _validate(r, n)
            out.append(r)
    return out


def _date(s, where):
    try:
        return dt.date.fromisoformat(s)
    except (TypeError, ValueError):
        raise Malformed(f"{where}: {s!r} is not a date (YYYY-MM-DD)")


def _validate(r, n):
    if not isinstance(r, dict):
        raise Malformed(f"line {n}: a record must be a JSON object")
    missing = REQUIRED - r.keys()
    if missing:
        raise Malformed(f"line {n}: missing {', '.join(sorted(missing))}")
    extra = r.keys() - RECORD_KEYS
    if extra:
        raise Malformed(f"line {n}: unknown key {', '.join(sorted(extra))}")
    d = r["derived"]
    if not isinstance(d, dict) or not d.get("title") or not d.get("version"):
        raise Malformed(f"line {n}: derived needs a title and a version")
    if not isinstance(r["from"], list) or not r["from"]:
        raise Malformed(f"line {n}: from must be a list of at least one source")
    for i, s in enumerate(r["from"]):
        if not isinstance(s, dict) or not s.get("title") or "version" not in s:
            raise Malformed(f"line {n}: from[{i}] needs a title and a version (null if unknown)")
    _date(r["recorded_on"], f"line {n}: recorded_on")
    if r.get("issued_on") is not None:
        _date(r["issued_on"], f"line {n}: issued_on")
    for key in ("claimed", "observed"):
        v = r.get(key)
        if v is None:
            continue
        if not isinstance(v, dict) or "on" not in v:
            raise Malformed(f"line {n}: {key} must be null or an object with 'on'")
        _date(v["on"], f"line {n}: {key}.on")


def check_log(records):
    """Problems with the register as a whole: reused ids, supersedes pointing forward."""
    problems, ids = [], set()
    for n, r in enumerate(records, start=1):
        if r["id"] in ids:
            problems.append(f"line {n}: id {r['id']} is used twice")
        if r.get("supersedes") and r["supersedes"] not in ids:
            problems.append(f"line {n}: supersedes {r['supersedes']}, which is not recorded earlier")
        ids.add(r["id"])
    return problems


def latest(records, on=None):
    """The records still in force on `on`: a record replaced by a later one is dropped.

    Records made after `on` are ignored, so the register can be read as it stood
    on an earlier day.
    """
    day = _date(on, "--on") if isinstance(on, str) else on
    kept = [r for r in records if day is None or _date(r["recorded_on"], "recorded_on") <= day]
    replaced = {r["supersedes"] for r in kept if r.get("supersedes")}
    return [r for r in kept if r["id"] not in replaced]


def verdicts(records, status, on):
    """One result per derived document and source. See the module docstring."""
    out = []
    for r in latest(records, on):
        flags = []
        claimed, observed = r.get("claimed"), r.get("observed")
        if claimed and (observed is None or _date(observed["on"], "observed.on") > _date(claimed["on"], "claimed.on")):
            flags.append("claimed-before-observed")
        if (r.get("issued_on") or claimed) and observed is None:
            flags.append("unobserved")
        for s in r["from"]:
            f = list(flags)
            if not s.get("as_stated"):
                f.append("not-in-document")
            cur = statuslog.current(status, s["title"], "edition", on)
            made = version_of(s.get("version"))
            if cur["status"] == "no-record":
                verdict, now = "source-unknown", None
            elif cur["status"] == "expired":
                verdict, now = "source-expired", None
            else:
                now = version_of(cur["value"])
                if made is None or now is None:
                    verdict = "source-unknown" if now is None else "stale"
                else:
                    verdict = "current" if made == now else "stale"
            out.append({
                "derived": f"{r['derived']['title']} {r['derived']['version']}",
                "source": s["title"],
                "made_from": s.get("version"),
                "source_now": now,
                "verdict": verdict,
                "flags": f,
                "record": r["id"],
            })
    return out


# --- 2. the version labels of a kit tree ----------------------------------------

def _reader(root, ref):
    """A function that returns a file's bytes (or None) from a directory or a git ref."""
    if ref is None:
        def read(path):
            p = os.path.join(root, path)
            if not os.path.exists(p):
                return None
            with open(p, "rb") as f:
                return f.read()
        return read

    def read(path):
        r = subprocess.run(["git", "-C", root, "show", f"{ref}:{path}"],
                           capture_output=True)
        return r.stdout if r.returncode == 0 else None
    return read


def _xlsx_strings(data):
    """Every text cell of the sheet named 'Start here', read with the standard library."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    rel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    with zipfile.ZipFile(BytesIO(data)) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{ns['m']}}}t")))
        book = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        targets = {e.get("Id"): e.get("Target") for e in rels}
        for sh in book.find("m:sheets", ns):
            if sh.get("name") != "Start here":
                continue
            target = targets[sh.get(rel)].lstrip("/")
            target = target if target.startswith("xl/") else "xl/" + target
            out = []
            for c in ET.fromstring(z.read(target)).iter(f"{{{ns['m']}}}c"):
                v = c.find("m:v", ns)
                if c.get("t") == "s" and v is not None:
                    out.append((c.get("r"), shared[int(v.text)]))
                elif c.get("t") == "inlineStr":
                    out.append((c.get("r"), "".join(t.text or "" for t in c.iter(f"{{{ns['m']}}}t"))))
            return out
    return []


KIT_LABEL = re.compile(r"(?:Kit|キット)\s*v(\d+(?:\.\d+)+)")
PAPER_LABEL = re.compile(r"What Breaks in a Citation(?:\*\*|』)?[^\n]{0,12}?[(（]v(\d+(?:\.\d+)+)")


def tree_labels(root, ref=None):
    """Where the tree names its own version and the paper's.

    Returns (kit, paper): lists of (place, version). A place that should carry a
    label and does not is listed with version None.
    """
    read = _reader(root, ref)
    kit, paper = [], []

    cff = read("CITATION.cff")
    if cff is not None:
        text = cff.decode("utf-8")
        top = re.search(r'^version:\s*"?([^"\n]+)"?', text, re.M)
        kit.append(("CITATION.cff version", top.group(1).strip() if top else None))
        for m in re.finditer(r'^\s+version:\s*"?([^"\n]+)"?', text, re.M):
            paper.append(("CITATION.cff references version", m.group(1).strip()))
    for name in ("README.md", "README_ja.md"):
        data = read(name)
        if data is None:
            continue
        head = "\n".join(data.decode("utf-8").splitlines()[:8])
        m = KIT_LABEL.search(head)
        kit.append((f"{name} header", m.group(1) if m else None))
        p = PAPER_LABEL.search(head)
        if p:
            paper.append((f"{name} header", p.group(1)))
    log = read("CHANGELOG.md")
    if log is not None:
        m = re.search(r"^## Kit v(\d+(?:\.\d+)+)", log.decode("utf-8"), re.M)
        kit.append(("CHANGELOG.md latest entry", m.group(1) if m else None))
    build = read("tools/build_kit.py")
    if build is not None:
        text = build.decode("utf-8")
        m = re.search(r'^KIT_VERSION\s*=\s*"([^"]+)"', text, re.M)
        kit.append(("tools/build_kit.py KIT_VERSION", m.group(1) if m else None))
        p = re.search(r'^PAPER\s*=\s*".*?v(\d+(?:\.\d+)+)', text, re.M)
        if p:
            paper.append(("tools/build_kit.py PAPER", p.group(1)))
    wb = read("kit/citation-provenance-kit.xlsx")
    if wb is not None:
        found = None
        for cell, text in _xlsx_strings(wb):
            m = KIT_LABEL.search(text)
            if m and found is None:
                found = (cell, m.group(1))
                p = PAPER_LABEL.search(text) or re.search(r"What Breaks in a Citation, v(\d+(?:\.\d+)+)", text)
                if p:
                    paper.append((f"workbook Start here {cell}", p.group(1)))
        kit.append((f"workbook Start here {found[0] if found else ''}".rstrip(), found[1] if found else None))
    return kit, paper


def tree_problems(kit, expected=None):
    """Kit labels that disagree.

    With `expected` (for example the tag being checked), every place that does
    not say it. Without it, nothing is assumed to be right: if the places do not
    all say the same, every place is returned, each with the value it gives.
    Returns a list of (place, value, expected-or-None).
    """
    if expected is not None:
        want = version_of(expected) or expected
        return [(place, v, want) for place, v in kit if v != want]
    if len({v for _, v in kit}) <= 1:
        return []
    return [(place, v, None) for place, v in kit]


# --- 3. the tags the README says exist -----------------------------------------

def claimed_tags(root, ref=None):
    data = _reader(root, ref)("README.md")
    if data is None:
        return []
    m = re.search(r"(?:Each release is tagged|Tags that existed[^:\n]*:)\s*\(([^)]*)\)", data.decode("utf-8"))
    return re.findall(r"`([^`]+)`", m.group(1)) if m else []


# --- command line --------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--log", help="register of derived documents (JSON Lines)")
    p.add_argument("--status", help="status log giving each source's current edition")
    p.add_argument("--on", help="YYYY-MM-DD (default: today)")
    p.add_argument("--tree", help="a kit directory (or git work tree with --ref)")
    p.add_argument("--ref", help="read the tree at this git ref instead of the working files")
    p.add_argument("--expect", help="the kit version the tree should name everywhere")
    p.add_argument("--tags", help="comma-separated tags that exist, or @FILE with one per line")
    p.add_argument("--json", action="store_true", help="print results as JSON")
    a = p.parse_args(argv)
    if not (a.log or a.tree):
        p.error("give --log (with --status) or --tree")
    if a.log and not a.status:
        p.error("--log needs --status")
    if a.tags and not a.tree:
        p.error("--tags needs --tree")
    on = a.on or dt.date.today().isoformat()
    report = False
    out = {}
    try:
        if a.log:
            records = load(a.log)
            status = statuslog.load(a.status)
            problems = check_log(records)
            res = verdicts(records, status, on)
            out["derived"] = res
            out["problems"] = problems
            for msg in problems:
                print("problem:", msg, file=sys.stderr)
                report = True
            if not a.json:
                print(f"derived documents as of {on}")
                for v in res:
                    flags = (" [" + ", ".join(v["flags"]) + "]") if v["flags"] else ""
                    print(f"  {v['verdict']:<15} {v['derived']}  <-  {v['source']} "
                          f"made from {v['made_from'] or '—'}, now {v['source_now'] or '—'}{flags}")
            report = report or any(v["verdict"] != "current" or v["flags"] for v in res)
        if a.tree:
            kit, paper = tree_labels(a.tree, a.ref)
            bad = tree_problems(kit, a.expect)
            out["kit_labels"] = kit
            out["paper_labels"] = paper
            out["kit_label_problems"] = bad
            where = f"{a.tree}" + (f" at {a.ref}" if a.ref else "")
            if not a.json:
                print(f"version labels in {where}")
                for place, v in kit:
                    print(f"  kit    {v or '—':<8} {place}")
                for place, v in paper:
                    print(f"  paper  {v or '—':<8} {place}")
                for place, v, want in bad:
                    if want is None:
                        print(f"  DISAGREE: {place} says {v or 'nothing'}")
                    else:
                        print(f"  DISAGREES: {place} says {v or 'nothing'}, expected {want}")
            report = report or bool(bad)
            if a.tags:
                if a.tags.startswith("@"):
                    with open(a.tags[1:], encoding="utf-8") as f:
                        have = {l.strip() for l in f if l.strip()}
                else:
                    have = {t.strip() for t in a.tags.split(",") if t.strip()}
                claimed = claimed_tags(a.tree, a.ref)
                missing = [t for t in claimed if t not in have]
                out["tags_claimed"], out["tags_missing"] = claimed, missing
                if not a.json:
                    print(f"  README says these tags exist: {', '.join(claimed) or '—'}")
                    for t in missing:
                        print(f"  CLAIMED, NOT FOUND: tag {t}")
                report = report or bool(missing)
    except (Malformed, OSError, json.JSONDecodeError, zipfile.BadZipFile, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if report else 0


if __name__ == "__main__":
    sys.exit(main())
