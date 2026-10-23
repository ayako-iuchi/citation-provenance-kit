#!/usr/bin/env python3
"""idcheck — identifiers, the namespace they belong to, and the key that makes them one thing.

A number is unique only inside a namespace. G.S.R. 206(E) names one
notification of 2015 and another of 2021; "#30" in this series names a post
and an entry of the method paper's log; echap06_vol1.pdf names chapter 6 of
two different years of the Economic Survey. Each of these passes an existence
check, because the other one exists too. The method paper's control is the
triple key: "An identifier is written as number, date, and instrument amended.
Never number alone." (§2-4). This tool generalises it: a namespace, a number,
and something the thing itself carries (what it amends, its title, its
edition, the hash of its contents).

register/namespaces.json declares each namespace: the fields of its key, the
words that name it in text ("Blog #", "log #", "ログ#"), whether a bare "#N"
can mean it, and which numbers exist or are planned. register/identifiers.jsonl
records individual identifiers with their keys. Records are appended, never
edited.

    python3 idcheck.py --check                        the register itself
    python3 idcheck.py --resolve gsr "206(E)" --key date=2021-03-24
    python3 idcheck.py --file a/echap06_vol1.pdf b/echap06_vol1.pdf
    python3 idcheck.py --scan post.txt [more.txt ...]

--check reports:
    number-shared    two records in one namespace share a number; the fields
                     that tell them apart are listed
    date-shared      two records in one namespace share a date and differ in
                     number (the complementary form, §2-2)
    name-shared      two files share a name and differ in content
    key-incomplete   a record lacks a field of its namespace's key, or has a
                     dash (not established) in it
    bare-overlap     two namespaces can both be meant by a bare "#N", and some
                     numbers exist (or are planned) in both
--resolve answers, for a namespace, a number and any key fields given:
    unique           one record
    ambiguous        more than one; the fields that would separate them are listed
    mismatch         the number exists, but not with the key given (and which
                     number has that key, if any)
    absent           no record has the number
--file hashes each file and finds it in the register by name and by content.
--scan finds each "#N" in the text and says which namespace it names:
    named            the text names the namespace ("Blog #30", "log #30"), or
                     the token continues a range or list that did
                     ("entries #26–#42", "Blog #19, #20 and #22–#24")
    absent           named, but the namespace has no such number, existing or
                     planned
    unqualified      bare, and only one namespace that a bare "#N" can mean
                     has N (existing or planned)
    ambiguous        bare, and more than one has it (existing or planned)
    unknown          bare, and none has it
A token continues the name of the token before it on the same line when only
a dash, a wave dash, a comma, 、, ・, a slash, "to", "and", "or", と or から
stands between them. Words after a token are not read: in "Blog #18 and #19 of
the log" the second token is read as a post. Only the "#N" form is read
("entry 30" is not), code spans are read like other text, and a fragment
inside a URL is skipped. It does not decide which namespace the writer meant;
the context may make it plain to a reader. It reports what the token alone
does not say.

It is a report, not a gate: exit 1 whenever anything is reported (in --scan,
anything but named; in --resolve, anything but unique; in --file, anything but
one record by content that is also the only record by name, so a right file
whose name another file shares is reported). Exit 2: a file could
not be read, or a record is malformed. Standard library only. CC0 1.0. Part of
the citation provenance kit (kit v1.12).
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NAMESPACES = os.path.join(ROOT, "register", "namespaces.json")
IDENTIFIERS = os.path.join(ROOT, "register", "identifiers.jsonl")

NS_KEYS = {"name", "what", "key", "names", "bare", "exists", "planned", "as_of", "source", "note"}
NS_REQUIRED = {"name", "what", "key", "bare"}
RECORD_KEYS = {"id", "namespace", "number", "key", "what", "source", "recorded_on",
               "recorded_by", "supersedes", "note"}
REQUIRED = {"id", "namespace", "number", "key", "what", "source", "recorded_on", "recorded_by"}
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
SHA256 = re.compile(r"[0-9a-f]{64}")
NOT_ESTABLISHED = {"—", "–", "-", ""}
# "#N": a hash, digits, and no Latin letter or digit after them. A hashtag
# (#TechBlog) has no digits after the hash; #1st is not a number. Japanese
# text may follow directly (#21の). Full-width ＃ and digits are read.
TOKEN = re.compile(r"[#＃]([0-9０-９]+)(?![0-9０-９A-Za-zＡ-Ｚａ-ｚ_])")
# Between two tokens of one range or list: a dash, a wave dash, "to", "and",
# "or", a comma, 、, ・ or a slash, with spaces.
JOIN = re.compile(r"^\s*(?:[–—\-〜~～,、・/]|to|and|or|から|と|及び|および)\s*$", re.I)


class Malformed(Exception):
    pass


def _norm(text):
    return unicodedata.normalize("NFKC", text or "")


def _ranges(spec, where):
    out = []
    for r in spec or []:
        if (isinstance(r, list) and len(r) == 2 and all(isinstance(x, int) and not isinstance(x, bool) for x in r)
                and r[0] <= r[1]):
            out.append((r[0], r[1]))
        elif isinstance(r, int) and not isinstance(r, bool):
            out.append((r, r))
        else:
            raise Malformed(f"{where}: a range is [low, high] or a number")
    return out


def load_namespaces(path=NAMESPACES):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, UnicodeDecodeError) as e:
        raise Malformed(f"{path}: {e}")
    except json.JSONDecodeError as e:
        raise Malformed(f"{path}: not JSON ({e.msg})")
    if not isinstance(data, dict) or not isinstance(data.get("namespaces"), list):
        raise Malformed(f"{path}: needs a list under 'namespaces'")
    out = {}
    for n, ns in enumerate(data["namespaces"], start=1):
        where = f"{path}, namespace {n}"
        if not isinstance(ns, dict):
            raise Malformed(f"{where}: not an object")
        bad = set(ns) - NS_KEYS
        if bad:
            raise Malformed(f"{where}: unknown keys {sorted(bad)}")
        missing = NS_REQUIRED - set(ns)
        if missing:
            raise Malformed(f"{where}: missing {sorted(missing)}")
        if not isinstance(ns["name"], str) or not ns["name"]:
            raise Malformed(f"{where}: name must be a string")
        if ns["name"] in out:
            raise Malformed(f"{where}: namespace {ns['name']!r} twice")
        if not (isinstance(ns["key"], list) and ns["key"] and all(isinstance(k, str) for k in ns["key"])):
            raise Malformed(f"{where}: key is a list of field names")
        if "number" in ns["key"]:
            raise Malformed(f"{where}: key lists the fields besides the number")
        for k in ("what", "source", "note"):
            if k in ns and not isinstance(ns[k], str):
                raise Malformed(f"{where}: {k} must be a string")
        if "as_of" in ns and not (isinstance(ns["as_of"], str) and DATE.fullmatch(ns["as_of"])):
            raise Malformed(f"{where}: as_of is not YYYY-MM-DD")
        if not isinstance(ns["bare"], bool):
            raise Malformed(f"{where}: bare is true or false")
        names = ns.get("names", [])
        if not (isinstance(names, list) and all(isinstance(x, str) and x.strip() for x in names)):
            raise Malformed(f"{where}: names is a list of strings")
        ns = dict(ns)
        ns["exists"] = _ranges(ns.get("exists"), where)
        ns["planned"] = _ranges(ns.get("planned"), where)
        out[ns["name"]] = ns
    # A word may name only one namespace.
    seen = {}
    for ns in out.values():
        for w in ns.get("names", []):
            k = _norm(w).strip().lower()
            if k in seen and seen[k] != ns["name"]:
                raise Malformed(f"{path}: {w!r} names both {seen[k]} and {ns['name']}")
            seen[k] = ns["name"]
    return out


def load(path, namespaces):
    """Read the register (JSON Lines). Blank lines are ignored."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = [(n, l) for n, l in enumerate(f, start=1) if l.strip()]
    except (OSError, UnicodeDecodeError) as e:
        raise Malformed(f"{path}: {e}")
    out, ids = [], set()
    for n, line in lines:
        where = f"{path}, line {n}"
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            raise Malformed(f"{where}: not JSON ({e.msg})")
        if not isinstance(rec, dict):
            raise Malformed(f"{where}: not an object")
        bad = set(rec) - RECORD_KEYS
        if bad:
            raise Malformed(f"{where}: unknown keys {sorted(bad)}")
        missing = REQUIRED - set(rec)
        if missing:
            raise Malformed(f"{where}: missing {sorted(missing)}")
        for k in ("id", "namespace", "number", "what", "source", "recorded_by"):
            if not isinstance(rec[k], str) or (k != "number" and not rec[k]):
                raise Malformed(f"{where}: {k} must be a string")
        if not rec["number"].strip():
            raise Malformed(f"{where}: number is empty")
        for k in ("supersedes", "note"):
            if rec.get(k) is not None and not isinstance(rec[k], str):
                raise Malformed(f"{where}: {k} must be a string or null")
        if rec["namespace"] not in namespaces:
            raise Malformed(f"{where}: namespace {rec['namespace']!r} is not declared")
        if not isinstance(rec["key"], dict):
            raise Malformed(f"{where}: key must be an object")
        allowed = set(namespaces[rec["namespace"]]["key"])
        extra = set(rec["key"]) - allowed
        if extra:
            raise Malformed(f"{where}: key fields {sorted(extra)} are not in namespace {rec['namespace']}'s key")
        for k, v in rec["key"].items():
            if v is not None and not isinstance(v, str):
                raise Malformed(f"{where}: key.{k} must be a string or null")
        if "date" in rec["key"] and rec["key"]["date"] not in (None, *NOT_ESTABLISHED):
            if not DATE.fullmatch(rec["key"]["date"]):
                raise Malformed(f"{where}: key.date is not YYYY-MM-DD")
            try:
                dt.date.fromisoformat(rec["key"]["date"])
            except ValueError:
                raise Malformed(f"{where}: key.date is not a date")
        if "sha256" in rec["key"] and rec["key"]["sha256"] not in (None, *NOT_ESTABLISHED):
            if not SHA256.fullmatch(rec["key"]["sha256"]):
                raise Malformed(f"{where}: key.sha256 is not 64 lower-case hex digits")
        if not (isinstance(rec["recorded_on"], str) and DATE.fullmatch(rec["recorded_on"])):
            raise Malformed(f"{where}: recorded_on is not YYYY-MM-DD")
        try:
            dt.date.fromisoformat(rec["recorded_on"])
        except ValueError:
            raise Malformed(f"{where}: recorded_on is not a date")
        if rec["id"] in ids:
            raise Malformed(f"{where}: id {rec['id']!r} used twice")
        ids.add(rec["id"])
        out.append(rec)
    by_id = {r["id"]: r for r in out}
    for r in out:
        s = r.get("supersedes")
        if s is None:
            continue
        if s not in ids:
            raise Malformed(f"record {r['id']}: supersedes {s!r}, which is not in the register")
        if s == r["id"]:
            raise Malformed(f"record {r['id']}: supersedes itself")
        if by_id[s]["namespace"] != r["namespace"]:
            raise Malformed(f"record {r['id']}: supersedes {s!r}, a record in another namespace")
        seen, cur = {r["id"]}, s
        while cur is not None:
            if cur in seen:
                raise Malformed(f"record {r['id']}: the chain of supersedes returns to {cur!r}")
            seen.add(cur)
            cur = by_id[cur].get("supersedes")
    targets = [r["supersedes"] for r in out if r.get("supersedes")]
    dup = {t for t in targets if targets.count(t) > 1}
    if dup:
        raise Malformed(f"records {sorted(dup)} are superseded more than once")
    return out


def current(records):
    gone = {r["supersedes"] for r in records if r.get("supersedes")}
    return [r for r in records if r["id"] not in gone]


def _established(v):
    return v is not None and _norm(v).strip() not in NOT_ESTABLISHED


def _same_number(a, b):
    return _norm(a).strip().lower() == _norm(b).strip().lower()


def _differs(recs, fields):
    return [f for f in fields if len({_norm(r["key"].get(f) or "—") for r in recs}) > 1]


def _in(n, ranges):
    return any(lo <= n <= hi for lo, hi in ranges)


# --- the register ------------------------------------------------------------

def check(records, namespaces):
    """Findings about the register itself, as a list of dicts."""
    out = []
    recs = current(records)
    for r in recs:
        missing = [f for f in namespaces[r["namespace"]]["key"] if not _established(r["key"].get(f))]
        if missing:
            out.append({"flag": "key-incomplete", "ids": [r["id"]], "namespace": r["namespace"],
                        "number": r["number"], "fields": missing})
    by_ns = {}
    for r in recs:
        by_ns.setdefault(r["namespace"], []).append(r)
    for ns, rs in sorted(by_ns.items()):
        fields = namespaces[ns]["key"]
        groups = {}
        for r in rs:
            groups.setdefault(_norm(r["number"]).strip().lower(), []).append(r)
        for g in groups.values():
            # A file's number is its name: name-shared below says it better.
            if len(g) > 1 and not {"name", "sha256"} <= set(fields):
                out.append({"flag": "number-shared", "ids": [r["id"] for r in g], "namespace": ns,
                            "number": g[0]["number"], "fields": _differs(g, fields)})
        if "date" in fields:
            dates = {}
            for r in rs:
                d = r["key"].get("date")
                if _established(d):
                    dates.setdefault(d, []).append(r)
            for d, g in sorted(dates.items()):
                if len({_norm(r["number"]).strip().lower() for r in g}) > 1:
                    out.append({"flag": "date-shared", "ids": [r["id"] for r in g], "namespace": ns,
                                "date": d, "numbers": [r["number"] for r in g]})
        if "name" in fields and "sha256" in fields:
            names = {}
            for r in rs:
                if _established(r["key"].get("name")):
                    names.setdefault(r["key"]["name"], []).append(r)
            for nm, g in sorted(names.items()):
                hashes = {r["key"].get("sha256") for r in g}
                if len(g) > 1 and (len(hashes) > 1 or not all(_established(h) for h in hashes)):
                    out.append({"flag": "name-shared", "ids": [r["id"] for r in g], "namespace": ns,
                                "name": nm, "fields": _differs(g, [f for f in fields if f != "name"])})
    bare = [ns for ns in namespaces.values() if ns["bare"]]
    for i, a in enumerate(bare):
        for b in bare[i + 1:]:
            spans = []
            for lo, hi in a["exists"] + a["planned"]:
                for lo2, hi2 in b["exists"] + b["planned"]:
                    if max(lo, lo2) <= min(hi, hi2):
                        spans.append([max(lo, lo2), min(hi, hi2)])
            if spans:
                out.append({"flag": "bare-overlap", "namespaces": [a["name"], b["name"]],
                            "numbers": _merge(spans)})
    return out


def _merge(spans):
    out = []
    for lo, hi in sorted(spans):
        if out and lo <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], hi)
        else:
            out.append([lo, hi])
    return out


# --- resolving ---------------------------------------------------------------

def resolve(records, namespaces, namespace, number, key=None):
    if namespace not in namespaces:
        raise Malformed(f"namespace {namespace!r} is not declared")
    key = key or {}
    bad = set(key) - set(namespaces[namespace]["key"])
    if bad:
        raise Malformed(f"{sorted(bad)} are not fields of namespace {namespace}'s key")
    recs = [r for r in current(records) if r["namespace"] == namespace]
    by_number = [r for r in recs if _same_number(r["number"], number)]

    for k, v in key.items():
        if not _established(v):
            raise Malformed(f"--key {k}: a dash or an empty value is not a value to match")

    def fits(r):
        # A field not established matches nothing.
        return all(_established(r["key"].get(k))
                   and _norm(r["key"][k]).strip().lower() == _norm(v).strip().lower()
                   for k, v in key.items())

    hits = [r for r in by_number if fits(r)]
    res = {"namespace": namespace, "number": number, "key": key,
           "by_number": [r["id"] for r in by_number], "ids": [r["id"] for r in hits]}
    if not by_number:
        res["verdict"] = "absent"
    elif not hits:
        res["verdict"] = "mismatch"
        res["key_matches"] = [{"id": r["id"], "number": r["number"]} for r in recs if key and fits(r)]
    elif len(hits) > 1:
        res["verdict"] = "ambiguous"
        res["separate_by"] = _differs(hits, namespaces[namespace]["key"])
    else:
        res["verdict"] = "unique"
    return res


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def find_file(records, path):
    try:
        digest = sha256_of(path)
    except OSError as e:
        raise Malformed(f"{path}: {e.strerror or e}")
    name = os.path.basename(path)
    recs = [r for r in current(records) if "sha256" in r["key"] or "name" in r["key"]]
    by_name = [r["id"] for r in recs if r["key"].get("name") == name]
    by_hash = [r["id"] for r in recs if r["key"].get("sha256") == digest]
    if len(by_hash) == 1:
        verdict = "unique"
    elif by_hash:
        verdict = "ambiguous"
    else:
        verdict = "absent"
    return {"file": path, "name": name, "sha256": digest, "by_name": by_name,
            "by_content": by_hash, "verdict": verdict}


# --- scanning text -----------------------------------------------------------

def _namers(namespaces):
    """(word, namespace) pairs, longest first, normalised."""
    pairs = [(_norm(w).lower(), ns["name"]) for ns in namespaces.values() for w in ns.get("names", [])]
    return sorted(pairs, key=lambda p: -len(p[0]))


def _named_by(before, namers):
    """The namespace a word right before the hash names, if any."""
    b = _norm(before).lower()
    for word, ns in namers:
        w = word.rstrip("#＃").rstrip()
        if not w:
            continue
        m = re.search(re.escape(w) + r"\s*$", b)
        if m:
            # The word must start at a boundary, so "catalog " is not "log "
            # and カタログ is not ログ: the character before it must not be of
            # the same script as the word's first character.
            if m.start() == 0 or _script(b[m.start() - 1]) is None \
                    or _script(b[m.start() - 1]) != _script(w[0]):
                return ns
    return None


def _script(c):
    if c.isascii() and c.isalnum():
        return "latin"
    if "\u30a0" <= c <= "\u30ff" or "\u31f0" <= c <= "\u31ff":
        return "katakana"
    if "\u3040" <= c <= "\u309f":
        return "hiragana"
    if "\u4e00" <= c <= "\u9fff":
        return "kanji"
    return None


def scan_text(text, namespaces):
    namers = _namers(namespaces)
    bare = [ns for ns in namespaces.values() if ns["bare"]]
    out = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        prev_line = None
        for m in TOKEN.finditer(line):
            # A fragment in a URL (https://x/#30) is not a reference.
            word_start = max(line.rfind(" ", 0, m.start()), line.rfind("\t", 0, m.start())) + 1
            if "://" in line[word_start:m.start()]:
                continue
            n = int(m.group(1))
            before = line[max(0, m.start() - 40): m.start()]
            ns = _named_by(before, namers)
            if not ns and prev_line and JOIN.match(line[prev_line[0]: m.start()]):
                ns = prev_line[1]
            if ns:
                exists = _in(n, namespaces[ns]["exists"])
                planned = _in(n, namespaces[ns]["planned"])
                known = bool(namespaces[ns]["exists"] or namespaces[ns]["planned"])
                tok = {"line": line_no, "col": m.start() + 1, "token": m.group(0), "number": n,
                       "verdict": "absent" if known and not (exists or planned) else "named",
                       "namespace": ns, "exists": exists, "planned": planned}
                prev_line = (m.end(), ns)
            else:
                cands = [b["name"] for b in bare if _in(n, b["exists"])]
                planned = [b["name"] for b in bare if _in(n, b["planned"]) and b["name"] not in cands]
                k = len(cands) + len(planned)
                verdict = "ambiguous" if k > 1 else "unqualified" if k == 1 else "unknown"
                tok = {"line": line_no, "col": m.start() + 1, "token": m.group(0), "number": n,
                       "verdict": verdict, "candidates": cands, "planned": planned}
                prev_line = None
            out.append(tok)
    return out


def summarise(tokens):
    s = {"named": 0, "absent": 0, "unqualified": 0, "ambiguous": 0, "unknown": 0}
    for t in tokens:
        s[t["verdict"]] += 1
    return s


# --- reporting ---------------------------------------------------------------

def _fmt_check(findings):
    lines = []
    for f in findings:
        if f["flag"] == "bare-overlap":
            spans = ", ".join(f"{a}" if a == b else f"{a}–{b}" for a, b in f["numbers"])
            lines.append(f"bare-overlap    {' and '.join(f['namespaces'])}: numbers {spans}")
        elif f["flag"] == "date-shared":
            lines.append(f"date-shared     {f['namespace']} {f['date']}: {', '.join(f['numbers'])} ({', '.join(f['ids'])})")
        elif f["flag"] == "name-shared":
            lines.append(f"name-shared     {f['namespace']} {f['name']}: {', '.join(f['ids'])}; differ in {', '.join(f['fields']) or '—'}")
        elif f["flag"] == "number-shared":
            lines.append(f"number-shared   {f['namespace']} {f['number']}: {', '.join(f['ids'])}; differ in {', '.join(f['fields']) or 'nothing recorded'}")
        else:
            lines.append(f"key-incomplete  {f['namespace']} {f['number']} ({f['ids'][0]}): {', '.join(f['fields'])}")
    return "\n".join(lines) or "nothing to report"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--namespaces", default=NAMESPACES, help="register/namespaces.json")
    p.add_argument("--log", default=IDENTIFIERS, help="register/identifiers.jsonl")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="report on the register itself")
    g.add_argument("--resolve", nargs=2, metavar=("NAMESPACE", "NUMBER"))
    g.add_argument("--file", nargs="+", metavar="PATH")
    g.add_argument("--scan", nargs="+", metavar="PATH")
    p.add_argument("--key", action="append", default=[], metavar="FIELD=VALUE",
                   help="with --resolve: a key field to match (repeatable)")
    p.add_argument("--all", action="store_true", help="with --scan: list named tokens too")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    try:
        namespaces = load_namespaces(args.namespaces)
        if args.key and not args.resolve:
            raise Malformed("--key goes with --resolve")
        if args.check:
            res = check(load(args.log, namespaces), namespaces)
            print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else _fmt_check(res))
            return 1 if res else 0
        if args.resolve:
            key = {}
            for kv in args.key:
                if "=" not in kv:
                    raise Malformed(f"--key {kv!r} is not FIELD=VALUE")
                k, v = kv.split("=", 1)
                key[k.strip()] = v
            res = resolve(load(args.log, namespaces), namespaces, args.resolve[0], args.resolve[1], key)
            if args.json:
                print(json.dumps(res, ensure_ascii=False, indent=2))
            else:
                extra = ""
                if res["verdict"] == "ambiguous":
                    extra = f"; separate by {', '.join(res['separate_by']) or '—'}"
                if res["verdict"] == "mismatch":
                    km = ", ".join(f"{m['number']} ({m['id']})" for m in res["key_matches"]) or "none"
                    extra = f"; the key given fits: {km}"
                print(f"{res['verdict']:10} {args.resolve[0]} {args.resolve[1]}"
                      f" — by number alone: {len(res['by_number'])}; {'with the key' if res['key'] else 'candidates'}: {', '.join(res['ids']) or 'none'}{extra}")
            return 0 if res["verdict"] == "unique" else 1
        if args.file:
            records = load(args.log, namespaces)
            res = [find_file(records, f) for f in args.file]
            if args.json:
                print(json.dumps(res, ensure_ascii=False, indent=2))
            else:
                for r in res:
                    print(f"{r['verdict']:10} {r['file']}  sha256 {r['sha256'][:12]}…"
                          f"  by name: {', '.join(r['by_name']) or 'none'}"
                          f"  by content: {', '.join(r['by_content']) or 'none'}")
            return 0 if all(r["verdict"] == "unique" and r["by_name"] == r["by_content"] for r in res) else 1
        results = []
        for path in args.scan:
            try:
                with open(path, encoding="utf-8") as f:
                    text = f.read()
            except (OSError, UnicodeDecodeError) as e:
                raise Malformed(f"{path}: {e}")
            toks = scan_text(text, namespaces)
            results.append({"file": path, "summary": summarise(toks), "tokens": toks})
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            for r in results:
                s = r["summary"]
                print(f"{r['file']}: named {s['named']}, absent {s['absent']}, unqualified {s['unqualified']}, "
                      f"ambiguous {s['ambiguous']}, unknown {s['unknown']}")
                for t in r["tokens"]:
                    if t["verdict"] == "named" and not args.all:
                        continue
                    if t["verdict"] in ("named", "absent"):
                        what = t["namespace"]
                    else:
                        what = ", ".join(t["candidates"] + [c + " (planned)" for c in t["planned"]]) or "—"
                    print(f"  {t['line']}:{t['col']}  {t['token']:5} {t['verdict']:11} {what}")
        return 1 if any(r["summary"]["named"] != len(r["tokens"]) for r in results) else 0
    except Malformed as e:
        print("error:", e, file=sys.stderr)
        return 2
    except RecursionError:
        print("error: input nested too deeply to read", file=sys.stderr)
        return 2
    except (OSError, ValueError, TypeError, KeyError) as e:
        print("error:", repr(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
