# *What Breaks in a Citation* v1.2: its annotations and its catch log

Every component-graded annotation in both editions of the paper (v1.2, 12 October 2026), read by `tools/notation.py` from text taken from the published PDFs with `pdftotext`, one page at a time. Kit v1.5.

Only the annotations are here, not the paper's text. The paper's body is CC BY 4.0 (Ayako Iuchi); this file, like the rest of the kit, is CC0.

| Field | What it is |
| --- | --- |
| `id` | `wbc-v1.2-<edition>-<n>`, numbered in reading order within each edition |
| `edition` | `en` or `ja`: which edition of the paper it was read from |
| `pdf_page` | The page of the PDF file, not the printed page number |
| `use` | Recorded by hand, not by the tool: `citation` (the paper grades a source it relies on), `example` (the paper shows the notation, §4), `quoted` (the paper quotes an annotation in its correction log) |
| `text` | The annotation as `notation.render()` writes it, not as extracted: the extracted text has stray spaces in places (e.g. `［存在: A ｜数値: B］`), and the grammar ignores whitespace, so they do not change the reading |
| `form` | `en`, `ja` or `plain` (a single grade, `[A]`) |
| `slots` | Component (English name), as written, grade, and whether the component is volatile |

Each edition has nine `citation` annotations, and they correspond one to one in order (`en-01` ↔ `ja-01` … `en-09` ↔ `ja-09`). The two in §1-1 grade Dahl et al. and Magesh et al.; the seven after them are in §3-2, on PDF pages 8–10 in English and 9–11 in Japanese. The Japanese edition has one more annotation than the English: `ja-14`, in correction entry #43 of its log, quotes `［数値: A｜版: —］` as an example of where a stray backtick had been printed.

## The catch log (kit v1.7)

`catch_log.csv` is the paper's published correction log as numbers, components, outcomes and phases only, read from Appendix A-2 (#1–#25, before release), A-3 (the confirmations of page) and A-6 (#26–#42, after release; #43–#44 are in the Japanese edition only). None of the paper's text is copied.

Two things are not in it. The paper's three abstentions (§7-5) have no number and no stated component (two are X-01 and X-02 in A-7; the third has no label). And the production-phase confirmations of every component except page: A-3 says they were recorded in the verification threads and not enumerated, and describes only page's. So a pre-release confirmation count of 0 in the output means "not enumerated", not "none"; only figure is stated to have had none.

| Column | What it is |
| --- | --- |
| `no` | The entry's number in the log; `A-3` for the one row that stands for uncounted confirmations |
| `edition` | Which editions carry the entry |
| `component` | As classified in the paper (grade D, §7-2); joined by `+` or `→` as printed |
| `outcome` | As printed in A-6; for #1–#25 "corrected", because A-2 has no outcome column and §7-2 calls all twenty-five corrections |
| `outcome_basis` | Where the outcome comes from, and its grade where it is inferred |
| `phase` | `pre` or `post` release |
| `count` | Empty: one entry. `uncounted` on the A-3 row: confirmations recorded but not counted |
| `note` | The four contested assignments (§A-4), and why the A-3 row is not numbered |

```
python3 tools/catchlog.py examples/method_paper_v1.2/catch_log.csv
```

## The annotations

```
python3 tools/notation.py paper_from_pdf.txt            # check the form
python3 tools/notation.py paper_from_pdf.txt --records  # the typed records
```
