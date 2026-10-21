# Four extraction reports, 24 July 2026

What an extractor returned in the four working threads that, in the author's records, ran verbatim extraction under the instruction in `kit/extraction_prompt_2026-07-24_ja.md`. The method paper (*What Breaks in a Citation* v1.2, §8-2) counts four such threads among nineteen; it does not name them. These four were identified as the extraction threads by an inventory of the production threads that Claude wrote on 26 July 2026.

| File | Source given to the extractor | Items requested |
| --- | --- | --- |
| `dpdp_rules.json` | Digital Personal Data Protection Rules, 2025 (English PDF, 18 pages) | 4 |
| `companies_accounts_rules.json` | Companies (Accounts) Rules, 2014, a compilation with amendments (38 pages) | 2 |
| `gfr_2017.json` | General Financial Rules 2017, updated up to 31.07.2024 (177 pages) | 5 |
| `engineering_analysis.json` | *Engineering Analysis Centre of Excellence v CIT* (Indian Kanoon, 115 pages), then a law firm's newsletter on it (4 pages): two reports | 3 |

## How they were transcribed

Claude copied them on 21 October 2026 from the threads, which are not published. Each file's `transcribed` field says what was left out. The rules:

- Only the extractor's reports. Its tool calls are not included. Where a thread has a second report in a short form, only the first is copied.
- Text is kept in the extractor's words, in the language it used. Markdown emphasis is removed; line breaks inside a quotation are joined with spaces. Long lists of case numbers and parts of long provisions are shortened and marked `[...]` with `"excerpt": true`.
- **Assigning text to fields is Claude's reading.** The 2026 instruction asked for a table, not these fields. Claude put the extractor's quotations under `quotes` and `footnotes`, its account of what it searched for under `search_record`, its descriptions of the source under `source`, and everything else it wrote under `remarks`. The one exception is `departures`: the extractor itself said it was departing from the instruction. None of the extractor's text is put under `outside`, because the 2026 instruction had no such field and the extractor marked nothing that way.
- **The item status is Claude's reading** of what the extractor said: `found`, `not_in_source` (the extractor said it was not in this PDF) or `undeterminable` (found, but something the request asked for could not be settled from this PDF: the attribution of footnotes 3–6 in the judgment).

A separate agent compared the transcriptions with the threads before release.

## Run

```
python3 tools/extractcheck.py examples/extraction_2026-07-24/*.json
```

Without the source PDFs, which are not in this kit, `extractcheck.py` can only say whether an identifier in the extractor's own words is shown by the report's own quotations, footnotes and search record, or given by the request. Something flagged may be printed in the PDF and simply not quoted; the DPDP Rules' gazette number may be such a case, and this kit cannot tell. What it flags is what the report asks a reader to take on trust.

## Licence

The transcriptions are CC0 1.0. The quotations inside them are from Indian statutory instruments and a judgment of the Supreme Court of India, and are not CC0; they are reproduced here as short excerpts for the purpose of checking the reports.
