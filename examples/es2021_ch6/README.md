# Example: Economic Survey 2020-21, Volume 1, chapter 6 (kit v1.4)

The chapter Hypothetical Technical Blog #21, *A Source Has Sources*, audited by hand. Here the same audit runs after retrieval.

| File | What it is |
| --- | --- |
| `lines.json` | Excerpted lines of five printed pages (181, 188, 189, 191, 194), with each line's position and height, made by `pdftotext -bbox-layout` and `tools/pdflines.py` |
| `loci.jsonl` | What `tools/loci.py` makes of them: 13 loci (paragraphs, section headings, footnotes), each with its printed pages and its words as a snapshot |
| `dependencies.jsonl` | What seven of those loci cite, one level down, recorded by hand. Footnotes 2 and 6 are recorded with the paragraphs that carry their markers |

## Run it

```
python3 tools/loci.py examples/es2021_ch6/lines.json --read-on 2026-10-20 > examples/es2021_ch6/loci.jsonl
python3 tools/loci.py examples/es2021_ch6/lines.json --naive        # the same lines, split without geometry
python3 tools/depaudit.py --loci examples/es2021_ch6/loci.jsonl --deps examples/es2021_ch6/dependencies.jsonl \
    --status register/status_log.jsonl --on 2026-10-20 \
    --query "How many days does it take to resolve a commercial contract in India?" -k 1
python3 tools/depaudit.py --loci examples/es2021_ch6/loci.jsonl --suggest "Doing Business"
```

## Where the lines came from

- File: `echap06_vol1.pdf` from https://www.indiabudget.gov.in/budget2021-22/economicsurvey/doc/vol1chapter/echap06_vol1.pdf, SHA-256 `7baa01f3f3c64ff3bb0ecdf85e914427f829ba9f940d4aee59657f623d54d7d9`. The same file name under a different path returns a different year's chapter, so the path and the hash both matter.
- Extracted on 20 October 2026 with pdftotext 24.02.0 (poppler). Another extractor, or another version, may give different characters and so different hashes.
- PDF page *n* is printed page *n* + 178. PDF page 1 carries no number.
- Only the lines this example needs are kept: the page heads; ¶6.5 and footnote 2 (p. 181); all of p. 188; the rest of ¶6.22 (p. 189); section heading (a) and ¶6.27 (p. 191); ¶6.32 (p. 194). `lines_kept` in each page gives the count.

## Who recorded the edges

The dependency records were drafted by Claude at the author's direction on 20 October 2026 and say so in `recorded_by`. They cover the five loci #21 relied on (¶6.19, ¶6.20, ¶6.21, section heading (c), ¶6.27) and the two paragraphs that cite the Doing Business report (¶6.5, ¶6.32). Any other locus is reported as **not audited**, which is not the same as citing nothing.

## Licence of the chapter's words

The words of the Economic Survey in `lines.json` and `loci.jsonl` are a publication of the Ministry of Finance, Government of India. They are reproduced here in excerpt so that the example runs as it stands, with the source named in every record. **They are not covered by the kit's CC0 dedication.** Everything else in this folder is CC0, like the rest of the kit.
