# Citation provenance kit

Reproduction kit for **What Breaks in a Citation** (v1.1, 26 July 2026) by Ayako Iuchi. Files made from the paper's v1.2 (12 October 2026) name it.
Kit v1.14 (24 October 2026) · **CC0 1.0** — no rights reserved. Copy, change and use it without asking or attributing. (Exceptions: quoted government, statutory and judicial text, and a few lines of a law firm's newsletter; see Licence.)

The paper argues that machine-assisted writing breaks less often in *what a source says* than in *what is true of the source*: its date, edition, page, identifier, or whether it is in force. This kit is the set of working materials for keeping that record while you write.

## What is in it

| Path | What it is |
| --- | --- |
| [`kit/citation-provenance-kit.xlsx`](kit/citation-provenance-kit.xlsx) | The kit in one workbook: catch log, components, grades & notation, cost calculator, and the paper's own 25-entry log as a worked example |
| [`csv/catch_log_template.csv`](csv/catch_log_template.csv) | The catch log columns and one example row, for any tool |
| [`csv/components.csv`](csv/components.csv) | The ten components, a definition each, and the sorting question |
| [`csv/example_log_v1.1.csv`](csv/example_log_v1.1.csv) | Appendix A-2 of the paper (v1.1), lightly condensed |
| [`csv/register_in_motion_template.csv`](csv/register_in_motion_template.csv) | Register of provisions in motion: status components, the issuer's source, last resolved, next check, and known pending changes (kit v1.1) |
| [`tools/citelint.py`](tools/citelint.py) | A small linter for documents that use component-graded citation: undefined log tokens, "the six above" counts, leftover drafting notes, Contents entries without headings, notation outside the vocabulary, and markup printed as text (kit v1.2) |
| [`schema/`](schema/) | JSON Schemas for a **snapshot** (the words of one edition at one locus, written once) and a **status assertion** (one dated statement about commencement, edition, existence, dependency or identifier) (kit v1.3) |
| [`register/status_log.jsonl`](register/status_log.jsonl) | The register of provisions in motion as an append-only log: the five v1.1 rows, then the finding of 12 October 2026 added beside the row it replaces (kit v1.3) |
| [`tools/statuslog.py`](tools/statuslog.py) | Answers "what had I recorded as of day X?" and "what may I rely on today?", and returns no value once a status has expired (kit v1.3) |
| [`tools/migrate_register.py`](tools/migrate_register.py) | Turns a v1.1 register CSV into the first lines of a status log, without inventing expiry dates (kit v1.3) |
| [`tools/pdflines.py`](tools/pdflines.py), [`tools/loci.py`](tools/loci.py) | Split a chapter into **loci** — numbered paragraphs, section headings, footnotes — using the page geometry, each with the printed pages it spans and its words as a snapshot (kit v1.4) |
| [`tools/retrieve.py`](tools/retrieve.py) | BM25 over the words of the loci only: a proposal, not a citation (kit v1.4) |
| [`tools/depaudit.py`](tools/depaudit.py) | The check after retrieval: words against their hash, recorded dependency edges one level down, and each cited work's status from the status log, as of a given day (kit v1.4) |
| [`schema/locus.schema.json`](schema/locus.schema.json), [`schema/dependency.schema.json`](schema/dependency.schema.json) | A locus (with its snapshot nested unchanged) and a dependency edge (kit v1.4) |
| [`examples/es2021_ch6/`](examples/es2021_ch6/) | The chapter that Blog #21 audited by hand, run through the pipeline. The chapter's words there are the Government of India's and are **not** CC0 (kit v1.4) |
| [`tools/notation.py`](tools/notation.py), [`schema/annotation.schema.json`](schema/annotation.schema.json) | Reads the notation, English and Japanese forms, with one grammar into typed records (component, grade, whether the component is volatile), checks its form (N0–N7), and rewrites it between the two forms (kit v1.5) |
| [`examples/method_paper_v1.2/`](examples/method_paper_v1.2/) | Every annotation in both editions of the paper, v1.2, as typed records (kit v1.5), and its published catch log as numbers, components, outcomes and phases (kit v1.7) |
| [`tools/nulleval.py`](tools/nulleval.py), [`evals/null/`](evals/null/), [`schema/null_item.schema.json`](schema/null_item.schema.json) | A test where an empty answer can be right: five questions, a scorer that counts filled and blanked slots apart and three kinds of empty, and a recorded run (kit v1.6) |
| [`tools/catchlog.py`](tools/catchlog.py) | Counts corrections and confirmations apart for each component, before and after release, and says which zeros mean nothing (kit v1.7); with `--fields`, how full each column is (kit v1.8) |
| [`examples/series_log/`](examples/series_log/) | The author's log after the paper's v1.2 (log #45–#62): date found, judgment columns, duration and phase only (kit v1.8); and log #45–#78 with only the date found, the duration and the phase (kit v1.13) |
| [`kit/extraction_prompt_2026-07-24_ja.md`](kit/extraction_prompt_2026-07-24_ja.md), [`_en.md`](kit/extraction_prompt_2026-07-24_en.md) | The verbatim-extraction instruction used in the source project on 24 July 2026, as written (Japanese) and translated (kit v1.9) |
| [`kit/extraction_prompt_v2_ja.md`](kit/extraction_prompt_v2_ja.md), [`_en.md`](kit/extraction_prompt_v2_en.md) | The instruction revised: "not in this PDF" with a search record, PDF and printed pages, and a separate field for anything from outside the source (kit v1.9) |
| [`tools/extractcheck.py`](tools/extractcheck.py), [`schema/extraction.schema.json`](schema/extraction.schema.json) | An extraction report as a record, and a check for identifiers the extractor states but the report does not show (kit v1.9) |
| [`examples/extraction_2026-07-24/`](examples/extraction_2026-07-24/) | The four extraction reports of 24 July 2026, transcribed. The quotations inside them are Indian statutory and judicial text and are **not** CC0 (kit v1.9) |
| [`tools/derivedcheck.py`](tools/derivedcheck.py), [`register/derived.jsonl`](register/derived.jsonl), [`schema/derived.schema.json`](schema/derived.schema.json) | A register of derived documents — summaries, READMEs, citation files, copies — with the edition of each source they were made from, and a check against the source's current edition in the status log; the kit's own version labels compared with each other; the tags the README lists compared with the tags that exist (kit v1.10) |
| [`tools/calccheck.py`](tools/calccheck.py), [`register/computed.jsonl`](register/computed.jsonl), [`schema/computed.schema.json`](schema/computed.schema.json) | A register of computed values — a ratio, a month counted from a period, a count — with their inputs, the operation and who did the arithmetic, and a check that recomputes each and flags what recomputing does not find, such as a value shown with its inputs' grade (kit v1.11) |
| [`tools/idcheck.py`](tools/idcheck.py), [`register/identifiers.jsonl`](register/identifiers.jsonl), [`register/namespaces.json`](register/namespaces.json), [`schema/identifier.schema.json`](schema/identifier.schema.json), [`schema/namespaces.schema.json`](schema/namespaces.schema.json) | A register of identifiers with the namespace each belongs to and the rest of its key (a date and what it amends, a title, a file's hash and edition), and a check that resolves a reference, reports numbers and file names that two things share, and finds each bare `#N` in a text that two namespaces could mean, and each named one the namespace does not have (kit v1.12) |
| [`tools/debtcheck.py`](tools/debtcheck.py), [`register/deferred.jsonl`](register/deferred.jsonl), [`schema/deferred.schema.json`](schema/deferred.schema.json) | A register of fixes found and put off to a later edition, the fixes made, and the editions published, and a report of how many are open for each document, how long the oldest has waited, and which an edition came out without (kit v1.13) |
| [`tools/elapsed.py`](tools/elapsed.py) | The clock time each tagged release spanned, from the commit times: elapsed time, not effort (kit v1.13) |
| [`tools/sessions.py`](tools/sessions.py) | Who was editing at the same time: the sessions named in the commits, their spans, two sessions that changed the same file on diverged lines of history, handoffs, and commits that name no session (kit v1.14) |
| [`tests/`](tests/) | Tests for the linter, the status log, the locus splitter, the check after retrieval, the notation reader, the null-answer scorer, the catch-log tally, the extraction check, the derived-document check, the computed-value check, the identifier check, the deferred-fix report, the elapsed-time report and the session report (`python3 -m pytest tests`; the schema tests need `jsonschema` and are skipped without it) |
| [`evidence/`](evidence/) | The linter's output on both editions of the paper, v1.1 and v1.2; the derived-document check (kit v1.10), the computed-value check (kit v1.11) and the identifier check (kit v1.12) on the kit's registers; the deferred-fix report, the durations of the series log and the elapsed time of each release, with the commit times they rest on (kit v1.13); the session report on the kit's own history, with the commits it rests on (kit v1.14) |
| [`tools/build_kit.py`](tools/build_kit.py) | The script that generates the workbook and CSVs (Python 3, `openpyxl`) |
| [`CHANGELOG.md`](CHANGELOG.md) | Dated revisions |
| [`LICENSE`](LICENSE) | CC0 1.0 Universal |

## How to use it, on the first day

1. **Name your components and close the list.** Start from the ten in the `Components` sheet. Delete what does not apply, add what your domain needs, and define every token you will use.
2. **Sort them with one question:** *can this become false without the document changing?* Those components (commencement, edition, existence, dependency — and, in other fields, retraction or restatement) must be re-resolved from the authoritative register when you write, not recalled.
3. **Grade per component, and only where grades diverge.** `[wording: A | commencement: —]`. The em dash means *not established, and not asserted*.
4. **Log every catch, confirmation and abstention.** Without confirmations there is no denominator. Without abstentions the discipline looks least effective exactly where it worked hardest.
5. **Fill "what would have happened" yourself, and keep the log open after release.**

## Columns the original log lacked

- **Did an existing rule fire?** Two rules failed to prevent the failure that produced them, and the log could not show it (Appendix B, §9-1).
- **Duration.** No effort was recorded, and it cannot be reconstructed (§8-1).
- **Stakes.** "A step of the argument collapses" versus "one footnote dies" (§7-1), as a field you can filter.
- **Phase.** The log closed at release, so post-publication defects went unnumbered (§9-7).

## The cost calculator

Hours = count × unit minutes ÷ 60, per action. The unit times are left blank on purpose. Supply your own. Any figure it produces is **grade D** and should be labelled so wherever it appears.

## The linter

```
python3 tools/citelint.py paper.md                                   # the author's Markdown source
python3 tools/citelint.py paper_from_pdf.txt --format rendered --lang ja  # text taken from the published file
```

It exits with status 1 when it reports anything, so it can run in CI. It reads only the text. It cannot tell whether a reading is right, whether a source is still in force, or whether two sentences that use different words make claims that contradict each other. On the paper's v1.1, it found 8 of the 17 defects later logged as log #26–#44 (excluding log #34, a confirmation, and log #35, a rule sharpened), and part of a ninth. It also found one that no reader had: in the Japanese edition, the Contents title of chapter 3 does not match the chapter heading. Hypothetical Technical Blog #19, *A Rule Is Not a Mechanism*, reports the run.

## The status log (kit v1.3)

The v1.1 register keeps one value and one "last resolved" date per row. When a value moves, the row has nowhere to keep the old one, and correcting it erases the record that you once believed otherwise. The status log never edits a line. A newer finding is a new line that names the line it supersedes.

```
python3 tools/statuslog.py register/status_log.jsonl --list
python3 tools/statuslog.py register/status_log.jsonl --subject "Japan — NTA Q&A on electronic books (books and documents)" --component edition --on 2026-10-11 --believed
python3 tools/statuslog.py register/status_log.jsonl --subject "India — DPDP Rules 2025, Rule 4 (consent managers)" --component commencement --on 2026-11-02
python3 tools/statuslog.py --verify-append yesterday.jsonl today.jsonl
```

The second command answers what had been recorded on 11 October; the third returns `"status": "expired"` and no value, because the row's next check has passed. An expired value is not replaced by the old one. Status never goes into a snapshot, so the words you index for search do not carry a status that can go stale.

`migrate_register.py` sets an expiry only where the "Next check" text gives a date or a regular interval. "On any change to the page" gives neither; that row's expiry stays null, and the query reports it as `no-expiry-stated`.

What it does not do: decide what to re-check, settle a conflict between sources, or grade anything. Those stay with you.

## The notation as typed records (kit v1.5)

```
python3 tools/notation.py paper_from_pdf.txt            # check the form
python3 tools/notation.py paper_from_pdf.txt --records  # one JSON line per annotation
python3 tools/notation.py draft_en.md --markdown --to ja  # write every annotation in the Japanese form, skipping code
```

A grade, the em dash and an absent slot are three different values: established, considered and not established, and not recorded. The tool keeps them apart and never turns one into another. It reads a bracket only if it is a single grade or names a known component before a colon, and leaves Markdown links alone. It checks only what the text shows: the grammar (N0), the vocabulary (N1), the grade (N2), the dash character (N3), at most three slots (N4), no component twice (N5), no split where every grade is the same (N6), and, as a notice, a first slot that is not established (N7). It cannot tell whether the first slot is the one the claim rests on, whether a split carries weight, whether a component is applied as defined, or what document a grade was given against. When checking, it exits with status 1 when N0–N6 report anything; it exits with 2 if the file cannot be read. Declare a domain's extension components with `--extend restatement-status`.

Each slot carries `volatile`, from `csv/components.csv`. The notation has no date, so a grade on a volatile component (edition, existence, commencement, dependency) holds only for the day it was resolved; that day belongs in the status log.

## A test where an empty answer can be right (kit v1.6)

```
python3 tools/nulleval.py evals/null/items.jsonl ANSWERS.json [--readings READINGS.json]
python3 tools/nulleval.py evals/null/items.jsonl --baseline fill   # or empty
```

Each slot's right answer is set against the evidence given with the question: a value, or one of three kinds of empty (`not-established`, `expired`, `no-record`). The scorer counts six outcomes and never adds them up; the two that matter most are `filled` (a value where the right answer was empty) and `blanked` (an empty where it was a value). Prose that opens like a refusal is scored `unread` until a reader has recorded what it does. See `evals/null/README.md` for the run of 20 October 2026.

## Two kinds of zero (kit v1.7)

```
python3 tools/catchlog.py LOG.csv            # the workbook's catch log exported as CSV, or any CSV with no, component, outcome, phase
python3 tools/catchlog.py examples/method_paper_v1.2/catch_log.csv
```

A log that counts only corrections shows zero both for a component that was checked and found sound and for one that was never checked. `catchlog.py` counts corrections and confirmations apart, for each component, before and after release, and names each cell `found`, `clean` (no correction, at least one confirmation), `other-only` (only an abstention or a rule sharpened) or `unexamined` (no row at all). It never adds the two together. It reads the workbook's Catch log sheet saved as CSV (UTF-8, or cp932 from Japanese Excel), English or Japanese component names, and reports a name it does not know (`--strict` makes that an error), because a misspelled component would otherwise show its real one as unexamined. The workbook's Outcome list has had "confirmed (no error found)" since v1.0; record confirmations in the same log as corrections. `examples/method_paper_v1.2/catch_log.csv` holds the method paper's published log (log #1–#42 in English, log #43–#44 in Japanese only) as numbers, components, outcomes and phases, without its text: before release, page is `clean` and figure `unexamined` (§7-3); after release, figure has two corrections and one confirmation. The paper's three abstentions (§7-5) are not in it, because the paper does not number them or give their components.

## The field nobody else can fill (kit v1.8)

```
python3 tools/catchlog.py LOG.csv --fields
python3 tools/catchlog.py examples/series_log/after_v1.2.csv --fields
```

`--fields` reports how full each column of a catch log is, before and after release: filled, not yet decided (or not recorded), or blank. It lists the entries with no decision in "what would have happened had it gone unnoticed" and in "stakes", and fills nothing in. The workbook and the CSV template have a new column after Stakes, "Who wrote 'what would have happened'?" (author; author chose from assistant's options; assistant; not yet decided), because the paper calls that field the one that cannot be delegated (§9-5), and an assistant can still draft it. `examples/series_log/after_v1.2.csv` holds the author's log after the paper's v1.2 (log #45–#62, not yet published in a paper) with only the date found, the judgment columns, the duration and the phase: three of eighteen entries have a decision, all chosen from an assistant's options.

## Not in this PDF (kit v1.9)

```
python3 tools/extractcheck.py REPORT.json [--source PAGES]
python3 tools/extractcheck.py examples/extraction_2026-07-24/*.json
```

The method paper's largest design decision was to run verbatim extraction in separate threads, under an instruction that forbade interpretation (§8-2). `kit/extraction_prompt_2026-07-24_ja.md` is that instruction as it was used, with an English translation; `kit/extraction_prompt_v2_*.md` revises it. In the four threads that used it, the quotations, the pages and "not found" held. Where the source ran out, the reports also stated things the source did not show: which notification inserted a provision that was not in the PDF, a statutory exemption, a comparison with a second document. The revision does not forbid that. It asks for "not in this PDF" with a search record, for the PDF page and the printed page, and for anything from outside the source in a field of its own, with its origin.

`extractcheck.py` reads a report in the form of `schema/extraction.schema.json`. It flags identifiers that appear in the extractor's own words (its remarks, its search record, its description of the source, its departures) but are not shown by the report's verbatim text (quotations, footnotes, the cover as quoted, and any passage the extractor sets in quotation marks, on its word that the passage is the source's; code marks never count, and in the search record only 「」 and “” do, since search terms are written in "" or code marks), not given by the request, and not declared as outside (X2). The search record counts as the extractor's own words: it is its account of the source. Each report is checked on its own. It checks identifiers, not what is said about them: "inserted by G.S.R. 205(E)" passes if a quotation shows 205(E) at all. The identifiers are gazette numbers, file numbers of office memoranda, case numbers, rule, section, paragraph and article numbers and Japanese 条 numbers, law-report citations, titles of rules, acts and regulations with their year, and dates in several forms; lists and ranges are expanded, and they are found inside Japanese text as well. It also flags an item reported not in the source with no search record (X3), an item reported found with no page (X4), and, given the source text, a quotation that is not on its page, matching PDF pages and printed pages separately (X1). Counts are of distinct identifiers. It cannot tell memory from the page; a flag means "not shown", not "wrong". `examples/extraction_2026-07-24/` holds the four reports of July 2026, transcribed; its README says how, and which parts are Claude's reading.

## Derived documents (kit v1.10)

```
python3 tools/derivedcheck.py --log register/derived.jsonl --status register/status_log.jsonl --on 2026-10-22
python3 tools/derivedcheck.py --tree .                          # this tree's own version labels
python3 tools/derivedcheck.py --tree . --ref v1.2 --expect v1.2 # a published tag, read through git
git ls-remote --tags origin > tags.txt
python3 tools/derivedcheck.py --tree . --tags @tags.txt          # the README's tag list against tags that exist
```

A summary, a README or a citation file copies facts about another document: its list of items, a count, its version, the date it was issued. When the source moves, the copy becomes wrong without a word of it changing. `register/derived.jsonl` records, for each derived document, which edition of each source it was made from, the words in the document that say so (verbatim, or null if it does not say), what it copies, the date it gives itself, any other document's statement that it was issued, and the day it was first seen. Like the status log, it is only appended to. The source's current edition comes from the status log (component `edition`), so the copy is compared with the same record as everything else that can become false without the document changing.

Each derived document gets one verdict per source: `current`, `stale` (made from another edition), `made-from-unknown` (the register does not say which edition), `source-unknown` (the status log has no edition for the source, or none that reads as a version) or `source-expired`; and flags: `not-in-document` (the document itself does not say what it was made from), `claimed-before-observed` (another document said it was issued before anyone had seen it), `unobserved` (said to be issued, never seen) and `replaced-by-vN` (the register holds a later version of the same document; this one may still be published). It is a report, not a gate: a copy made from an older edition stays stale for as long as it is recorded, so the exit status is 1 whenever anything is not current. The first rows are the series' own. The one-page summary of the domain paper, v1.0, named on its last line the edition it was made from; the domain paper moved to v1.1 two days later (26 July), and the line went uncorrected until the summary's v1.1 was issued on 13 October, 79 days later. The comparison that found it is entry #32 of the method paper's log, in the paper's v1.2 of 12 October. The method paper's v1.2 recorded the summary's v1.1 as issued on 12 October; it was issued on 13 October (log #49). The kit itself is recorded as made from two editions of the paper, and gets two verdicts.

`--tree` collects the version labels the kit gives itself (CITATION.cff, both READMEs, CHANGELOG, the workbook's Start here sheet, read with the standard library, and `build_kit.py`) and reports them when they disagree; without `--expect` it does not assume which one is right. Run on the published tags, it finds the two failures already logged where they were: at v1.2 the citation file said 1.1.1 (log #47) and the workbook 1.1 (log #65); from v1.3 to v1.7 the workbook said 1.1 (log #65); and at v1.9 the workbook said 1.8 (`evidence/derivedcheck_2026-10-22.txt`). A test runs it on this tree, so a release whose labels disagree fails its own tests. The edition of the paper each place names is listed and not judged; the register says which files come from which edition. `--tags` compares the tags the README lists with tags you give it: a comma-separated list, or a file with one tag per line or the output of `git ls-remote --tags origin` as it stands.

It does not say what in a stale document is wrong; that is a reading. It sees only documents someone recorded. It cannot open short links such as lnkd.in, so when a document was first seen is recorded by a person.

## Computed values (kit v1.11)

```
python3 tools/calccheck.py --log register/computed.jsonl --status register/status_log.jsonl --on 2026-10-23 --all
```

`--all` includes records that a later record replaces (here, the README's count of 18, replaced by 17); without it, only current records are checked.

A ratio, a month counted from a period, a count of items, a number of days: a computed value has no source of its own. It has inputs, an operation, and someone who did the arithmetic. The paper says such a value is "neither A nor D" (§4-6) and that it has no rule for arithmetic (§9-3). Written as a bare number beside a grade, the value takes the grade of its inputs, and nothing says who computed it. Recomputing it checks the arithmetic, not where the number came from.

`register/computed.jsonl` records, for each computed value, the value as shown and where; its inputs, each with its source, its grade, any range ("a little over") or alternative (two dates for one notification), any pending change, and the status-log line it depends on; the operation, from a closed list (divide, add months, days between, minutes between, count), evaluated without `eval()`; the precision shown; who did the arithmetic (`source`, `author`, `assistant` or `unknown`); what documents say about that; and the grade printed beside the value. It is only appended to.

Each value gets `recomputes` or `differs`, and flags: `grade-borrowed` (someone other than the source did the arithmetic, and the value is shown beside a grade A, with neither the grade nor the value saying whose arithmetic it is; within the closed vocabulary the form is `[figure: A | attribution: D]`, and fixed phrases such as "author's arithmetic" also count; only fixed forms are read, so "not computed" is not understood), `operator-unknown`, `claims-disagree` (documents disagree about who computed it, or with the record), `sensitive` (an input's range or alternative changes the value as shown; otherwise it is robust to them), `if-pending` (a recorded pending change would change it), and `input-expired` / `input-unrecorded` for the status-log line an input depends on. It is a report, not a gate: the exit status is 1 whenever anything is flagged.

The first records are the series' own, and every value in them recomputes. The domain paper's "about 1.6 per cent" turned out not to be computed at all: the judgment states it (「約一・六パーセント」), so the record gives the source as the one that computed it, and lists the method paper's description of it as the author's derivation as a disagreeing claim (entry #76 of the author's log after v1.2). The domain paper's "May 2027" is the author's arithmetic on a period, shown beside a grade A (`grade-borrowed`); the status log's identical month says, in its value, whose it is, and is not flagged. The status log's other month, "November 2026" for Rule 4, recorded the same day, does not say so, and is flagged. Both Mays would become November 2026 if the period were cut to twelve months, and both are robust to the two recorded publication dates. The README's "18 defects" (entry #62) is a right sum on a wrong rule for what to count: the check marks it `sensitive` to the exclusions. The 79 days of the v1.10 README are `sensitive` to the other end the record holds: the method paper dated the summary's v1.1 a day early (log #49). The output is in `evidence/calccheck_2026-10-23.txt`.

It cannot tell whether a source states a value itself; the 1.6 per cent was recorded as derived for three months. It does not say whether an operation is the right one for the argument (whether total assets is the right denominator); that is a reading. It sees only values someone recorded.

## Identifiers (kit v1.12)

```
python3 tools/idcheck.py --check
python3 tools/idcheck.py --resolve gsr "206(E)" --key date=2021-03-24
python3 tools/idcheck.py --file path/to/echap06_vol1.pdf
python3 tools/idcheck.py --scan post.txt
```

A number is unique only inside a namespace. The paper's control for statutory instruments is the triple key: "An identifier is written as number, date, and instrument amended. Never number alone." (§2-4). The same failure has other shapes. Kit v1.2's README cited a post as Hypothetical Technical Blog #18 after the series was renumbered, and the post it meant had become Blog #19 (log #48). The Economic Survey's chapter 6 is `echap06_vol1.pdf` under two paths, one for 2018-19 and one for 2020-21: the same file name, two editions. And this series writes a bare `#` for its posts and for the entries of the method paper's log, whose numbers now overlap.

`register/namespaces.json` declares each namespace: the fields of its key besides the number, the words that name it in text (`Blog #`, `log #`, `ログ#`), whether a bare `#N` can mean it, and which numbers exist or are planned. `register/identifiers.jsonl` records identifiers with their keys; a dash means a field is not established. It is only appended to.

`--check` reports `number-shared` (two records in one namespace share a number, with the fields that separate them), `date-shared` (they share a date and differ in number, the paper's complementary form), `name-shared` (two files share a name and differ in content), `key-incomplete` (a key field is missing or a dash) and `bare-overlap` (two namespaces a bare `#N` can mean, and the numbers they share). `--resolve` answers `unique`, `ambiguous` (with the fields that would separate the candidates), `mismatch` (the number exists, not with the key given, and which number has that key) or `absent`. `--file` hashes each file and finds it by name and by content. `--scan` finds each `#N` in a text and calls it `named` (the text names the namespace, or the token continues a range or list that did), `absent` (named, but the namespace has no such number, existing or planned), `unqualified` (bare, and only one namespace has the number or plans it), `ambiguous` (bare, and more than one has it or plans it) or `unknown`. Words after a token are not read, so in "Blog #18 and #19 of the log" the second is read as a post. Only the `#N` form is read: "entry 30" is not. A fragment inside a URL is skipped; code spans are read. `--file` reports a right file whose name another file shares. It does not decide which one the writer meant; the context may make that plain to a reader. It reports what the token alone does not say. It is a report, not a gate: the exit status is 1 whenever anything is reported.

The first records are the series' own: G.S.R. 205(E) and 206(E) of 2021 and 206(E) of 2015 (§2-2); the two office memoranda of 29 October 2021, one of whose subjects is not established; Blog #18 and #19, for log #48; and the two chapters named `echap06_vol1.pdf`. The 2020-21 file's hash is the one `examples/es2021_ch6/lines.json` recorded; the 2018-19 file has not been hashed from here, and is `key-incomplete` until it is. From v1.12 this README names the namespace of every number it writes in the `#N` form, and so do the components list and the register's own text; a test scans them. Three records written earlier the same day gave numbers without their namespace or one source for facts from three; they stand as written, and later records supersede them. The output is in `evidence/idcheck_2026-10-23.txt`, with counts from the posts Blog #17–#31, which are not in the kit.

It reads only what is recorded and what is written. Which third field identifies a thing is a choice the writer makes; a hash changes when a file is re-saved with the same contents, as a PDF with new metadata is. Published posts are not changed.

## Deferred fixes and elapsed time (kit v1.13)

```
python3 tools/debtcheck.py register/deferred.jsonl --on 2026-10-24 --list
python3 tools/catchlog.py examples/series_log/through_78.csv --fields
python3 tools/elapsed.py --git . --named
```

The paper says the cost of the discipline "is not a smooth per-citation tax. It arrives in lumps, late, when a rule fires on work already believed finished" (§8-4), and advises a duration field "on day one" (§8-1). The kit has had that column since v1.0. In the author's log after v1.2, log #45 to log #78, it reads 「記録なし」 (not recorded) in all 34 entries. A column a person has to fill in is a rule, not a mechanism.

`register/deferred.jsonl` records four kinds of line: a fix found and put off, with the log entry, the document, the place, when it is to be made ("next edition", "next revision" or a named edition), any condition and the dates found and recorded; a fix made, with the day the edition carrying it was published; a deferral closed without a fix (its condition was not met, or it was decided not to make it), with the reason; and an edition published. It is only appended to. A log entry counts as a deferral when its outcome leaves the fix out of an edition that is published, or released without it, and names a later one ("not changed in v1.2; v1.3 will add", "to be fixed in the next edition"). A fix made in the version being prepared when the entry was written is not a deferral.

`debtcheck.py` reports, for each document as of a day, how many deferrals are open (conditional ones apart), paid and withdrawn, the oldest open one and its age in days, and any that are overdue. A deferral to "next edition" is overdue once an edition of the document has been published on a later day than the deferral was recorded (an edition of the same day is taken to be the one the fix was found in); a deferral to a named edition is overdue once that edition has been published. When the log does not record the date found, the date recorded is used and the report says so. "As of a day" reads the dates the lines carry; an edition with no recorded date is listed and never makes anything overdue. It counts and dates; it does not say how long a fix will take. `--check` refuses any other `fix_in` that says "next" or 次, a payment in an edition the register does not have or dated otherwise than that edition, a withdrawal without a reason, an edition recorded twice, and a deferral closed twice. A line recorded wrongly is not edited: a withdrawal says so, and a new deferral replaces it.

The first records are the log's own: sixteen fixes deferred to the method paper's next edition (two conditional), one to the domain paper's next revision, and two that the kit left out of v1.2 and made in v1.3 (log #46 and log #47), with the kit's releases from v1.0 to v1.12. None is overdue: no edition of either paper has come out since. The register holds what the log records as deferred; a fix put off in a working note and never logged is not in it.

`elapsed.py` reads the commit times and reports, for each tagged release, the commits that belong to it (reachable from the tag and from no tag on an earlier commit), the first and the tagged commit, and the clock time between; `--named` starts the span at the first commit whose subject names the release, and counts every commit from there. The span ends at the tagged commit, not when the tag was made. It is elapsed time, not effort: it does not separate work from waiting, knows nothing of work before the first commit or outside git, and counts parallel work once. v1.0 to v1.2 were each one commit, so each shows no time at all; v1.3 shows more than a week, most of it a pause. `--dump` writes the commit times as TSV, so the report can be reproduced without the repository. The outputs of all three tools are in `evidence/debtcheck_2026-10-24.txt`; the elapsed-time sections are computed from the commit times stored in `evidence/git_times_2026-10-24.tsv`.

`catchlog.py --fields` now also reads a marker followed by one note in brackets, such as 「記録なし（2026-10-20には判断待ちとして挙がっていた）」, as not recorded, as it already did for a dash followed by a note. Text after the note makes it an answer, for a dash as for a marker.

## Who was editing (kit v1.14)

```
python3 tools/sessions.py --git .
python3 tools/sessions.py --from evidence/sessions_commits_2026-10-24.tsv
```

The paper's log closed at release (§9-7); from v1.2 it stays open, and the author's log after v1.2 is kept in the same way. An open log records failures of the process as well as of the documents. On 13 October 2026 two sessions changed the same lines of both READMEs eight minutes apart, on two branches (c9a9823 on `main`, the number of a post only; fdd8f9c on `kit-v1.3`, its number and title), and the first wrote nothing in this changelog until the second recorded it (c538dae; log #48). The response was a rule kept in the series' handoff memo: one thread at a time is the sole editor.

Every commit in this repository ends with a `Claude-Session` line naming the session that made it. `sessions.py` reads, for every commit on every branch, the time, the session and the files changed (for a merge, against its first parent). It reports each session's span (first to last commit); pairs of sessions whose spans overlap, and within them, commits of the two that changed the same file when neither had the other in its history and one was made while the other session was active; handoffs, where a session's first commit changed a file the previous session's last commit had changed; and commits with no session line. `--trailer` names another trailer. `--dump` writes the commits as TSV, with their parents, so the report can be reproduced without the repository. The exit status is 1 when two sessions changed the same file on diverged lines, or a commit has no session.

On this repository it finds eight sessions and one overlap, from the evening of 12 October to the morning of 13 October, with two such pairs on the READMEs; none after. A commit made on top of the other session's commit, as the 12 October changelog entry after the v1.2 release was, is not reported. The output is in `evidence/sessions_2026-10-24.txt`.

It sees commits only. A session can be open before its first commit and after its last; documents edited outside git (the series' theme list, memo and posts) leave nothing here; several agents inside one session share its name. Two spans that overlap say that two sessions committed in the same period, not that they conflicted.

## What this kit does not do

It verifies nothing. It records what your verification acts produced. A document can be perfectly graded and still misread.

## Posts that use the kit

Hypothetical Technical Blog, *Citation provenance* (English, on note):

- Blog #17 — [What Broke Was the Provenance, Not the Claim](https://note.com/ayako_iuchi/n/nb5dbd0aa502b)
- Blog #18 — [Commencement Is a Cache-Invalidation Problem](https://note.com/ayako_iuchi/n/n6cbb36bb35c1) (the register of provisions in motion, added in kit v1.1)
- Blog #19 — [A Rule Is Not a Mechanism](https://note.com/ayako_iuchi/n/n5adfbe0c66f8) (the linter, kit v1.2)
- Blog #20 — [Fixed Words, Moving Status](https://note.com/ayako_iuchi/n/ne5747d7bcd77) (the status log, kit v1.3)
- Blog #21 — [A Source Has Sources](https://note.com/ayako_iuchi/n/n7a82eee7a8af)
- Blog #22 — [The Chunk Is the Citation](https://note.com/ayako_iuchi/n/n380de7d3e282) (loci, retrieval and the dependency check after it, kit v1.4)
- Blog #23 — [The Component Is the Type](https://note.com/ayako_iuchi/n/ndacfe00e9263) (the notation as typed records, kit v1.5)
- Blog #24 — [Not Established Is an Answer](https://note.com/ayako_iuchi/n/n7d7ca5a8837b) (a test where an empty answer can be right, kit v1.6)
- Blog #31 — [Recomputing Is Not Citing](https://note.com/ayako_iuchi/n/nf8adb5ccde85) (computed values and who did the arithmetic, kit v1.11; published on 23 October 2026, after v1.11 was released and tagged).
- Blog #32 — [A Number Is Not a Key](https://note.com/ayako_iuchi/n/ncf262340dc74) (identifiers, namespaces and the identifier check, kit v1.12; published on 23 October 2026, after v1.12 was released and tagged). Blog #25–#30 are published; their links are to be added.

Each release is tagged by the author on GitHub after its release commit is on `main`; until then it has no tag. Tags that existed when this README was last changed (24 October 2026): (`v1.0`, `v1.1`, `v1.1.1`, `v1.2`, `v1.3`, `v1.4`, `v1.5`, `v1.6`, `v1.7`, `v1.8`, `v1.9`, `v1.10`, `v1.11`, `v1.12`). The v1.12 tag points at 146d887, the v1.12 release commit; the author made it on GitHub on 23 October 2026 (11:33 JST, as GitHub records it; the tag is lightweight and carries no time of its own). The v1.11 tag points at 19ec6f7, the v1.11 release commit; the author made it on 23 October 2026, at 09:36 JST. The v1.10 tag points at 1b57c34, the v1.10 release commit; the author made it on 23 October 2026. The v1.9 tag is a lightweight tag and carries no time of its own; it was made with the v1.9 release, which GitHub records as published on 22 October at 13:22:40 JST, about 23½ hours after the release commit; Hypothetical Technical Blog #27, which cites v1.9, was published in that gap. Blog #19, #20 and #22–#24 name the version they describe; check out that tag to see the kit as they saw it. Blog #17, #18 and #21 name no version; when they were published (13–14 October 2026) the default branch held v1.2. Blog #22, #23 and #24 were published on 20 October 2026, after v1.4, v1.5 and v1.6 respectively were released.

## Sources

- What Breaks in a Citation — links listed since kit v1.0: [English](https://lnkd.in/p/giTfeMUh) · [日本語](https://lnkd.in/p/gFUXFv2w); v1.2, as cited in Hypothetical Technical Blog #28: [English](https://lnkd.in/p/gjQ2RAPW) · [日本語](https://lnkd.in/p/gW5xwpFK). Which edition each link opens has not been checked from here.
- What Your Buyer Is Defending Against (the source project) — [English](https://lnkd.in/p/gHNjBuCd) · [日本語](https://lnkd.in/p/gF-kd9DF)

The example log is the author's English translation. The original log was kept in Japanese and governs; from v1.2 of the paper (12 October 2026) it is published as Appendix A-2 of the Japanese edition. In v1.1 it was referenced but not published. Its component and rule columns are the author's classification, applied afterwards (grade D). Four entries are contested; see the paper, Appendix A-4.

## Licence

The kit is dedicated to the public domain under CC0 1.0, except for text it quotes from others, which is not covered by CC0 and which the kit grants no permission to reuse:

- the words of the Economic Survey 2020-21, a publication of the Government of India, in `examples/es2021_ch6/` (kit v1.4) and in the tests and `evals/null/` that use them (kit v1.4–v1.6);
- the quotations inside the extraction reports in `examples/extraction_2026-07-24/` (kit v1.9): Indian statutory instruments, the General Financial Rules, a judgment of the Supreme Court of India, and a few lines of a law firm's newsletter (its title, copyright line and one case citation), reproduced as the extractor quoted them.
- a few words of a judgment of the Supreme Court of Japan (20 January 1994) quoted in `register/computed.jsonl` and `evidence/calccheck_2026-10-23.txt` (kit v1.11).

The transcriptions around those quotations are CC0. The papers it accompanies are licensed separately (the body of *What Breaks in a Citation* under CC BY 4.0).

## Commit messages

Commits made with Claude end with two lines: `Co-Authored-By: Claude …` and `Claude-Session: https://claude.ai/code/session_…`. The session link is the author's own record of the conversation in which the change was made, kept for looking back. It opens only for the author and has not been shared; to anyone else it shows a sign-in page or nothing. It is not a source for anything in the kit. What was decided is in `CHANGELOG.md` and in the files themselves.

## Corrections

Corrections are welcome — open an issue. They are published as dated revisions in `CHANGELOG.md`, not silent edits.

*A discipline that is licensed is a discipline that is not adopted.*
