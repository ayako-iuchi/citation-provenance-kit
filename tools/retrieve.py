#!/usr/bin/env python3
"""retrieve — rank loci for a question with BM25. A proposal, not a citation.

The index sees only the words of each locus (its snapshot). It holds no status
and no dependencies, so nothing it returns can carry a status that has gone
stale. What a returned locus rests on is looked up afterwards (depaudit.py).

BM25 as in Robertson and Zaragoza, "The Probabilistic Relevance Framework: BM25
and Beyond" (2009), with k1 = 1.2 and b = 0.75 and the idf
log((N - n + 0.5) / (n + 0.5) + 1). Tokens are lowercased runs of letters and
digits. There is no stemming: "persist" does not match "persists".

Usage:
    python3 retrieve.py LOCI.jsonl "question" [-k 3]

Standard library only. CC0 1.0. Part of the citation provenance kit (v1.4).
"""
import argparse
import json
import math
import re
import sys
from collections import Counter

TOKEN = re.compile(r"[0-9a-z]+")


def tokens(text):
    return TOKEN.findall(text.lower())


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


class BM25:
    def __init__(self, loci, k1=1.2, b=0.75):
        self.loci, self.k1, self.b = loci, k1, b
        self.docs = [Counter(tokens(l["snapshot"]["wording"])) for l in loci]
        self.lens = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lens) / len(self.lens)
        df = Counter(t for d in self.docs for t in d)
        n = len(self.docs)
        self.idf = {t: math.log((n - c + 0.5) / (c + 0.5) + 1) for t, c in df.items()}

    def score(self, query, i):
        d, s = self.docs[i], 0.0
        for t in tokens(query):
            if t in d:
                f = d[t]
                s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.lens[i] / self.avg))
        return s

    def search(self, query, k=3):
        ranked = sorted(((self.score(query, i), i) for i in range(len(self.docs))), key=lambda x: (-x[0], x[1]))
        return [{"id": self.loci[i]["id"], "label": self.loci[i]["label"], "score": round(s, 3)}
                for s, i in ranked[:k] if s > 0]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("loci")
    ap.add_argument("question")
    ap.add_argument("-k", type=int, default=3)
    args = ap.parse_args(argv)
    for r in BM25(load(args.loci)).search(args.question, args.k):
        print(json.dumps(r, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
