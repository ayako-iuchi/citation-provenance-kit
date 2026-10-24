#!/usr/bin/env python3
"""silentcheck — files that changed in a release and that its changelog never names.

The kit's changelog opens: "Revisions are dated and kept visible. Nothing is
changed silently." The method paper and its one-page summary make the same
promise. A promise like that is a rule, and nothing checked it.

For each pair of neighbouring tags (or the two you give), this tool lists the
files that differ between them, and the lines added to the changelog in the same
range, and reports each changed file that those lines do not name. A file is
named when the added lines contain

    its path                       tools/idcheck.py
    its file name                  idcheck.py
    a directory above it, as such  `examples/es2021_ch6/` (followed by a space,
                                   a quotation mark or the end of a word)
    an alias declared for it       README.md and README_ja.md: "README" or
                                   "READMEs"; the workbook: "workbook"

Aliases are declared in a JSON file (default register/silent_aliases.json):
{"path": ["word", ...]}. A word matches as a whole word, in any case.

It reports names, not content. A file named in one line about something else
counts as named, and a changelog that names a file and describes the change
wrongly passes. What it finds is a change the changelog never mentions at all.

Headings in the changelog ("## README update — 2026-10-24") do not name
anything; only the lines under them do. The changelog itself is not checked
against itself.

Usage:
    python3 silentcheck.py --git REPO [--changelog CHANGELOG.md] [--aliases FILE]
                           [--from TAG --to TAG] [--json]

Exit status: 0; 1 if any changed file is not named; 2 on unreadable input.

Standard library only (git is needed). CC0 1.0. Part of the citation provenance
kit (v1.15).
"""
import argparse
import json
import os
import re
import subprocess
import sys


def _version_key(tag):
    return ([int(n) for n in re.findall(r"\d+", tag)] or [0], tag)


def _git(repo, *args):
    try:
        r = subprocess.run(["git", "-C", repo, "-c", "core.quotePath=false", *args],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
    except OSError as e:
        raise ValueError(f"git: {e}") from None
    if r.returncode != 0:
        raise ValueError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def load_aliases(path):
    if not path:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError) as e:
        raise ValueError(f"{path}: {e}") from None
    if not isinstance(d, dict) or not all(isinstance(k, str) and isinstance(v, list) and all(isinstance(w, str) and w for w in v)
                                          for k, v in d.items()):
        raise ValueError(f"{path}: expected an object of path -> list of words")
    return d


def _bounded(text, s, after_dir=False):
    lead = r"(?<![\w./-])"
    tail = r"(?=[\s`'\"),;:]|$)" if after_dir else r"(?![\w/-]|\.\w)"
    return re.search(lead + re.escape(s) + tail, text, re.M) is not None


def named(path, text, aliases):
    """How the added changelog text names `path`, or None."""
    if _bounded(text, path):
        return "path"
    base = path.rsplit("/", 1)[-1]
    if base != path and _bounded(text, base):
        return "file name"
    parts = path.split("/")
    for i in range(len(parts) - 1, 0, -1):
        d = "/".join(parts[:i]) + "/"
        if _bounded(text, d, after_dir=True):
            return f"directory {d}"
    for w in aliases.get(path, []):
        if re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", text, re.I):
            return f"alias {w}"
    return None


def check_range(repo, a, b, changelog="CHANGELOG.md", aliases=None):
    aliases = aliases or {}
    files = [f for f in _git(repo, "diff", "--name-only", "--no-renames", a, b).splitlines() if f]
    diff = _git(repo, "diff", "-U0", a, b, "--", changelog)
    added = "\n".join(l[1:] for l in diff.splitlines()
                      if l.startswith("+") and not l.startswith("+++") and not l[1:].lstrip().startswith("#"))
    rows = []
    for f in files:
        if f == changelog:
            continue
        rows.append({"path": f, "named_by": named(f, added, aliases)})
    return {"from": a, "to": b, "changed": len(rows), "changelog_lines": len(added.splitlines()) if added else 0,
            "unnamed": [r["path"] for r in rows if not r["named_by"]], "files": rows}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--git", metavar="REPO", required=True)
    ap.add_argument("--changelog", default="CHANGELOG.md")
    ap.add_argument("--aliases", help="JSON of path -> words (default: register/silent_aliases.json in REPO, if present)")
    ap.add_argument("--from", dest="a")
    ap.add_argument("--to", dest="b")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        if bool(a.a) != bool(a.b):
            raise ValueError("--from and --to go together")
        alias_path = a.aliases
        if alias_path is None:
            default = os.path.join(a.git, "register", "silent_aliases.json")
            alias_path = default if os.path.exists(default) else None
        aliases = load_aliases(alias_path)
        if a.a:
            pairs = [(a.a, a.b)]
        else:
            tags = sorted((t for t in _git(a.git, "tag", "--list", "v*").split() if t), key=_version_key)
            if len(tags) < 2:
                raise ValueError("fewer than two tags")
            pairs = list(zip(tags, tags[1:]))
        results = [check_range(a.git, x, y, a.changelog, aliases) for x, y in pairs]
    except ValueError as e:
        print(f"silentcheck: {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("Changed files that the changelog lines added in the same range do not name. Names, not content.")
        for r in results:
            print(f"{r['from']}..{r['to']}: {r['changed']} file(s) changed, {len(r['unnamed'])} not named"
                  + (f": {', '.join(r['unnamed'])}" if r["unnamed"] else ""))
        total = sum(len(r["unnamed"]) for r in results)
        print(f"not named in all: {total}")
    return 1 if any(r["unnamed"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
