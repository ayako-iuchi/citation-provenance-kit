# Five extraction reports from four threads, 24 July 2026

What an extractor returned in the four working threads that ran verbatim extraction, on 24 July 2026, under the instruction in `kit/extraction_prompt_2026-07-24_ja.md`. The method paper (*What Breaks in a Citation* v1.2, §8-2) counts four such threads among nineteen; it does not name them. These four were identified as the extraction threads by an inventory of the production threads that Claude wrote on 26 July 2026 from a search of the author's conversations. That inventory gives one of them (the DPDP thread) under an identifier that does not open, and another (the GFR thread) under a shortened identifier only; the threads were opened by their full identifiers, found in another record of the same day. That they are the four §8-2 counts is a reading, not something the paper says.

| File | Source given to the extractor | Items requested |
| --- | --- | --- |
| `dpdp_rules.json` | Digital Personal Data Protection Rules, 2025 (English PDF, 18 pages) | 4 |
| `companies_accounts_rules.json` | Companies (Accounts) Rules, 2014, a compilation with amendments (38 pages) | 2 |
| `gfr_2017.json` | General Financial Rules 2017, updated up to 31.07.2024 (177 pages) | 5 |
| `engineering_analysis.json` | *Engineering Analysis Centre of Excellence v CIT* (Indian Kanoon, 115 pages); then, in the same thread, a law firm's newsletter on it (4 pages). Two reports | 3 |

## How they were transcribed

Claude copied them on 21 October 2026 from the threads, which are not published. Each file's `transcribed` field says what it leaves out. The rules:

- The extractor's report, whole: every table cell, heading, paragraph, list item and quotation, in its words and its language. Two quotations are shortened, and marked `[...]` with `"excerpt": true`: the list of 86 tagged appeal numbers in the judgment, and a Hindi note whose text layer was garbled. Markdown emphasis is removed; code marks (backticks) are kept; line breaks inside a quotation are joined with spaces.
- The extractor's tool calls are not included. Where a thread has a second report in a short form (all four do), it is not transcribed.
- **Assigning text to fields is Claude's reading.** The 2026 instruction asked for a table, not these fields. Text the extractor set out as quotation of the source (block quotations, the quoted notes and footnotes) is under `quotes` and `footnotes`, on the item it was quoted for. What it says it searched for and found is under `search_record`. Its description of the source is under `source`. Everything else it wrote, including the headings it put over quotations and the table cells that only say "below" or "none", is under `remarks`, in order. Where the extractor quoted something inside its own sentence (in 「」, “”, "" or backticks), the sentence is kept whole in `remarks` or `search_record`, and the quotation marks are kept. `departures` holds only text in which the extractor itself said it was departing from the instruction. Nothing is under `outside`: the 2026 instruction had no such field, and the extractor marked nothing that way.
- **The item status is Claude's reading** of what the extractor said: `found`; `partial` (some of what the item named is in this PDF and some is not: the newsletter has the judgment's date but no case numbers or judges); `not_in_source` (the extractor said it was not in this PDF). `undeterminable` is not used here.

A separate agent compared a first draft of these transcriptions with the threads on 21 October 2026. It found a sentence that defines the item cut out of an excerpt (the mandate in Rule 149), headings and table cells left out without saying so, a quotation that showed the extractor's account of the footnotes wrongly by shortening it, a wrong statement that the newsletter report quoted nothing, and statuses that did not fit. This version transcribes each report whole and was written to answer those findings.

## Run

```
python3 tools/extractcheck.py examples/extraction_2026-07-24/*.json
```

Without the source PDFs, which are not in this kit, `extractcheck.py` can only say whether an identifier in the extractor's own words is shown by the report's own quotations, or given by the request. Each report is checked on its own: in the newsletter report, the paragraph numbers of the judgment are flagged, though the judgment report quotes them. Something flagged may be printed in the PDF and simply not quoted; the DPDP Rules' gazette number may be such a case, and this kit cannot tell. And something not flagged is not thereby checked: a passage the extractor sets in quotation marks counts as shown, on the extractor's word.

## Licence

The transcriptions are CC0 1.0. The quotations inside them are not: they are Indian statutory instruments, the Government of India's General Financial Rules, a judgment of the Supreme Court of India, and a few lines of a law firm's newsletter (its title and copyright line, as the extractor gave them). They are reproduced here as the extractor quoted them, for the purpose of checking its reports.
