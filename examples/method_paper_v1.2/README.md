# The annotations of *What Breaks in a Citation* v1.2

Every component-graded annotation in both editions of the paper (v1.2, 12 October 2026), read by `tools/notation.py` from text taken from the published PDFs with `pdftotext`, one page at a time. Kit v1.5.

Only the annotations are here, not the paper's text. The paper's body is CC BY 4.0 (Ayako Iuchi); this file, like the rest of the kit, is CC0.

| Field | What it is |
| --- | --- |
| `id` | `wbc-v1.2-<edition>-<n>`, numbered in reading order within each edition |
| `pdf_page` | The page of the PDF file, not the printed page number |
| `use` | Recorded by hand, not by the tool: `citation` (the paper grades a source it relies on), `example` (the paper shows the notation, §4), `quoted` (the paper quotes an annotation in its correction log) |
| `text` | The annotation with whitespace normalised. The extracted text has stray spaces in places (e.g. `［存在: A ｜数値: B］`); the grammar ignores whitespace, so they do not change the reading |
| `slots` | Component (English name), as written, grade, and whether the component is volatile |

Each edition has nine `citation` annotations, and they correspond one to one in order (`en-01` ↔ `ja-01` … `en-09` ↔ `ja-09`). The two in §1-1 grade Dahl et al. and Magesh et al.; the seven after them are §3-2 (PDF pages 8–10 in English, 9–11 in Japanese). The Japanese edition has one more annotation than the English: `ja-14`, in correction entry #43 of its log, quotes `［数値: A｜版: —］` as an example of where a stray backtick had been printed.

```
python3 tools/notation.py paper_from_pdf.txt            # check the form
python3 tools/notation.py paper_from_pdf.txt --records  # the typed records
```
