#!/usr/bin/env python3
"""depaudit — the check after retrieval: what does each retrieved locus stand on?

For each locus (named, or returned by retrieve.py for a question) it:

  1. checks that the words still hash to the snapshot's recorded SHA-256, and,
     if a quotation is given, that the quotation is in those words;
  2. follows the recorded dependency edges one level down — the locus's own,
     and those of the footnotes anchored in it;
  3. attaches the status of each cited work from the status log, as of the day
     asked (statuslog.current: ok, no-expiry-stated, expired or no-record);
  4. writes one row in the shape Hypothetical Technical Blog #21 proposed: the
     locus, what it cites, the depth, the result, and what was not looked at.

It does not decide what a locus cites. Edges are recorded by a person, with a
date, in a dependency file. A locus with no record is reported as not audited,
which is not the same as "cites nothing". It does not grade a status either: the
status value is printed as recorded.

`--suggest NAME` lists the loci whose words contain NAME. That is how a name
match would find edges. It is shown for comparison and never used as an edge.

Usage:
    python3 depaudit.py --loci L --deps D --status S --on YYYY-MM-DD --query "question" [-k 3]
    python3 depaudit.py --loci L --deps D --status S --on YYYY-MM-DD --locus ID [--quote "words"]
    python3 depaudit.py --loci L --suggest "Doing Business"

Standard library only. CC0 1.0. Part of the citation provenance kit (v1.4).
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import retrieve  # noqa: E402
import statuslog  # noqa: E402


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def suggest(loci, name):
    """Loci whose words contain `name` (case-insensitive). A candidate, never an edge."""
    n = name.lower()
    return [l["id"] for l in loci if n in l["snapshot"]["wording"].lower()]


def audit(locus_id, loci, deps, log, on, quote=None):
    by_id = {l["id"]: l for l in loci}
    loc = by_id[locus_id]
    snap = loc["snapshot"]
    hash_ok = hashlib.sha256(snap["wording"].encode("utf-8")).hexdigest() == snap["wording_sha256"]
    members = [locus_id] + [f for f in loc["footnotes"] if f in by_id]
    records = [d for d in deps if d["locus"] in members]
    cited, unknowns = [], []
    for d in records:
        if d["cites"] is None:
            continue
        if d.get("status_subject"):
            st = statuslog.current(log, d["status_subject"], d.get("status_component", "existence"), on)
            status = {"status": st["status"], "value": st["value"],
                      "assertion": st["assertion"]["id"] if st["assertion"] else None}
        else:
            status = {"status": "no-record", "value": None, "assertion": None}
        cited.append({"cites": d["cites"], "how": d["how"],
                      "via": None if d["locus"] == locus_id else d["locus"], "status": status})
        unknowns.append(f"what {d['cites']} itself rests on (depth 2, not audited)")
    if not records:
        result = "not audited: no dependency record for this locus"
    elif not cited:
        result = "audited at depth 1: cites no work"
    else:
        on_record = sum(1 for c in cited if c["status"]["status"] != "no-record")
        result = f"audited at depth 1: cites {len(cited)} work(s); {on_record} with a status on record"
    return {
        "locus": locus_id, "label": loc["label"], "printed_pages": loc["printed_pages"],
        "wording_sha256_ok": hash_ok,
        "quote_found": None if quote is None else quote in snap["wording"],
        "depth": 1 if records else 0, "as_of": on,
        "dependencies": cited, "result": result,
        "unknowns": unknowns,
        "recorded_by": sorted({d["recorded_by"] for d in records}),
        "recorded_on": sorted({d["recorded_on"] for d in records}),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--loci", required=True)
    ap.add_argument("--deps")
    ap.add_argument("--status")
    ap.add_argument("--on")
    ap.add_argument("--query")
    ap.add_argument("-k", type=int, default=3)
    ap.add_argument("--locus", action="append")
    ap.add_argument("--quote")
    ap.add_argument("--suggest")
    args = ap.parse_args(argv)
    loci = load_jsonl(args.loci)
    if args.suggest:
        print(json.dumps({"name": args.suggest, "loci_containing_it": suggest(loci, args.suggest)}, ensure_ascii=False))
        return 0
    deps, log = load_jsonl(args.deps), statuslog.load(args.status)
    ids = args.locus or []
    if args.query:
        hits = retrieve.BM25(loci).search(args.query, args.k)
        print(json.dumps({"query": args.query, "retrieved": hits}, ensure_ascii=False))
        ids += [h["id"] for h in hits]
    for i in ids:
        print(json.dumps(audit(i, loci, deps, log, args.on, args.quote), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
