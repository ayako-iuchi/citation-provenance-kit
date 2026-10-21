# The verbatim-extraction instruction, revised (v2, kit v1.9)

This revises the instruction of 24 July 2026 (`extraction_prompt_2026-07-24_en.md`) in the light of what happened in the four working threads that used it. In those threads the verbatim text, the pages and "not found" held. Where the source ran out, knowledge from outside the source, and judgments about how one source related to another, came in as explanation (Hypothetical Technical Blog #27).

The revision does not forbid outside knowledge. It moves it to a field of its own and makes it carry its origin. A guess about where the missing text lives can be useful. The trouble is when it sits inside the extraction report looking like extraction.

What changed:

- "Not found" becomes "not in this PDF". The extractor does not say the item does not exist, and must give a search record: what it searched for, how many hits, how far it looked.
- Pages are given twice: the PDF page and the printed page.
- Anything the source does not say (which notification inserted a provision, a formal title, another edition, a legal assessment) goes only in the field "From outside this source", with where it came from.
- The title, issuer and edition are copied verbatim from the cover or colophon first, and given from that.
- A shortened quotation is marked […], and anything else, such as the procedure, goes under "Remarks".
- A second document gets a report of its own. The extractor does not compare the two.
- When an instruction cannot be followed (for copyright, say), the extractor names the line and the reason under "Departures from the instruction".

The machine-readable form is `schema/extraction.schema.json`; `tools/extractcheck.py` checks it.

This is a translation of `extraction_prompt_v2_ja.md`; where the two differ, the Japanese governs.

```text
From the PDF below, extract the specified provisions "verbatim".
[Must follow]
- Verbatim quotation of the provision only. Add no summary, paraphrase or interpretation whatsoever.
- If there are amendment-history footnotes, copy those verbatim as well (they contain important information).
- If a provision cannot be found, report "not in this PDF". Do not write that it does not exist. Do not fill in by guessing.
- For each item not found, give a search record (the strings searched for, the number of hits, the range checked).
- No judgment of importance, and no explanation of relations to other provisions or other documents, is needed.
- Do not write anything the source does not say (which notification inserted something, a formal title, another edition, a legal assessment, and so on) in the verbatim, page or not-found fields. If you write it, write it only under "From outside this source", with its origin (memory, or the name of the other document).
- If another document is added, make a separate report for that document alone. Do not compare documents.
- If you shorten a quotation, mark the gap […] and say so under "Remarks".
- If you cannot follow any of these instructions, say which line and why under "Departures from the instruction".
[Handling the PDF]
- First check the page count and whether there is a text layer (pdfinfo / pdffonts).
- If there is no text layer, OCR it (tesseract).
- Identify the page of each provision both as the PDF page and as the printed page.
[Items to extract]
1. [provision number]
2. [provision number]
[Report format]
Fill in the table below and return it.
| Item | Content |
|---|---|
| Cover and colophon, verbatim | (the places that give the title, issuer and edition, exactly as in the original, with their pages) |
| Formal title of the source | (from the verbatim above) |
| Issuing body | (from the verbatim above; if absent, "not stated") |
| Edition / last amended | (from the verbatim above) |
| Total pages | (PDF pages / last printed page) |
| Page of the provision | (PDF page / printed page) |
| Verbatim quotation | (exactly as in the original) |
| Amendment-history footnotes | (exactly as in the original, if any) |
| Items not found | ("not in this PDF", with the search record) |
| From outside this source | (if any; each with its origin) |
| Departures from the instruction | (if any; which line, and why) |
| Remarks | (anything that fits nowhere above, such as the procedure) |
```

Name the items by provision number only. In the threads of July 2026 the items carried descriptions of their content, such as "the audit-trail, edit-log and cannot-be-disabled requirements, and the financial year they apply from". A description is the requester's expectation, and for the extractor it is something to check. If you add one, put it on a separate line as "Expected (to be checked)". In `schema/extraction.schema.json` it goes under `expected`, not `target`: identifiers in `target` count as given by the request, identifiers in `expected` do not count.

CC0 1.0. Part of the citation provenance kit (v1.9).
