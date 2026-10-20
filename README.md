# Citation provenance kit

Reproduction kit for **What Breaks in a Citation** (v1.1, 26 July 2026) by Ayako Iuchi.
Kit v1.6 (20 October 2026) · **CC0 1.0** — no rights reserved. Copy, change and use it without asking or attributing. (One exception, from kit v1.4: see Licence.)

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
| [`examples/es2021_ch6/`](examples/es2021_ch6/) | The chapter #21 audited by hand, run through the pipeline. The chapter's words there are the Government of India's and are **not** CC0 (kit v1.4) |
| [`tools/notation.py`](tools/notation.py), [`schema/annotation.schema.json`](schema/annotation.schema.json) | Reads the notation, English and Japanese forms, with one grammar into typed records (component, grade, whether the component is volatile), checks its form (N0–N7), and rewrites it between the two forms (kit v1.5) |
| [`examples/method_paper_v1.2/`](examples/method_paper_v1.2/) | Every annotation in both editions of the paper, v1.2, as typed records (kit v1.5), and its published catch log as numbers, components, outcomes and phases (kit v1.7) |
| [`tools/nulleval.py`](tools/nulleval.py), [`evals/null/`](evals/null/), [`schema/null_item.schema.json`](schema/null_item.schema.json) | A test where an empty answer can be right: five questions, a scorer that counts filled and blanked slots apart and three kinds of empty, and a recorded run (kit v1.6) |
| [`tools/catchlog.py`](tools/catchlog.py) | Counts corrections and confirmations apart for each component, before and after release, and says which zeros mean nothing (kit v1.7, unreleased) |
| [`tests/`](tests/) | Tests for the linter, the status log, the locus splitter, the check after retrieval, the notation reader, the null-answer scorer and the catch-log tally (`python3 -m pytest tests`; the schema tests need `jsonschema` and are skipped without it) |
| [`evidence/`](evidence/) | The linter's output on both editions of the paper, v1.1 and v1.2 |
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

It exits with status 1 when it reports anything, so it can run in CI. It reads only the text. It cannot tell whether a reading is right, whether a source is still in force, or whether two sentences that use different words make claims that contradict each other. On the paper's v1.1, it found 8 of the 17 defects later logged as #26–#44 (excluding #34, a confirmation, and #35, a rule sharpened), and part of a ninth. It also found one that no reader had: in the Japanese edition, the Contents title of chapter 3 does not match the chapter heading. Hypothetical Technical Blog #19, *A Rule Is Not a Mechanism*, reports the run.

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

## Two kinds of zero (kit v1.7, unreleased)

```
python3 tools/catchlog.py LOG.csv            # the workbook's catch log exported as CSV, or any CSV with no, component, outcome, phase
python3 tools/catchlog.py examples/method_paper_v1.2/catch_log.csv
```

A log that counts only corrections shows zero both for a component that was checked and found sound and for one that was never checked. `catchlog.py` counts corrections and confirmations apart, for each component, before and after release, and names each cell `found`, `clean` (no correction, at least one confirmation), `other-only` (only an abstention or a rule sharpened) or `unexamined` (no row at all). It never adds the two together. It reads the workbook's Catch log sheet saved as CSV (UTF-8, or cp932 from Japanese Excel), English or Japanese component names, and reports a name it does not know (`--strict` makes that an error), because a misspelled component would otherwise show its real one as unexamined. The workbook's Outcome list has had "confirmed (no error found)" since v1.0; record confirmations in the same log as corrections. `examples/method_paper_v1.2/catch_log.csv` holds the method paper's published log (#1–#42 in English, #43–#44 in Japanese only) as numbers, components, outcomes and phases, without its text: before release, page is `clean` and figure `unexamined` (§7-3); after release, figure has two corrections and one confirmation. The paper's three abstentions (§7-5) are not in it, because the paper does not number them or give their components.

## What this kit does not do

It verifies nothing. It records what your verification acts produced. A document can be perfectly graded and still misread.

## Posts that use the kit

Hypothetical Technical Blog, *Citation provenance* (English, on note):

- #17 — [What Broke Was the Provenance, Not the Claim](https://note.com/ayako_iuchi/n/nb5dbd0aa502b)
- #18 — [Commencement Is a Cache-Invalidation Problem](https://note.com/ayako_iuchi/n/n6cbb36bb35c1) (the register of provisions in motion, added in kit v1.1)
- #19 — [A Rule Is Not a Mechanism](https://note.com/ayako_iuchi/n/n5adfbe0c66f8) (the linter, kit v1.2)
- #20 — [Fixed Words, Moving Status](https://note.com/ayako_iuchi/n/ne5747d7bcd77) (the status log, kit v1.3)
- #21 — [A Source Has Sources](https://note.com/ayako_iuchi/n/n7a82eee7a8af)
- #22 — [The Chunk Is the Citation](https://note.com/ayako_iuchi/n/n380de7d3e282) (loci, retrieval and the dependency check after it, kit v1.4)
- #23 — [The Component Is the Type](https://note.com/ayako_iuchi/n/ndacfe00e9263) (the notation as typed records, kit v1.5)

Each release is tagged (`v1.0`, `v1.1`, `v1.1.1`, `v1.2`, `v1.3`, `v1.4`, `v1.5`, `v1.6`). #19, #20, #22 and #23 name the version they describe; check out that tag to see the kit as they saw it. #17, #18 and #21 name no version; when they were published (13–14 October 2026) the default branch held v1.2. #22 and #23 were published on 20 October 2026, after v1.4 and v1.5 respectively were released.

## Sources

- What Breaks in a Citation — [English](https://lnkd.in/p/giTfeMUh) · [日本語](https://lnkd.in/p/gFUXFv2w)
- What Your Buyer Is Defending Against (the source project) — [English](https://lnkd.in/p/gHNjBuCd) · [日本語](https://lnkd.in/p/gF-kd9DF)

The example log is the author's English translation. The original log was kept in Japanese and governs; from v1.2 of the paper (12 October 2026) it is published as Appendix A-2 of the Japanese edition. In v1.1 it was referenced but not published. Its component and rule columns are the author's classification, applied afterwards (grade D). Four entries are contested; see the paper, Appendix A-4.

## Licence

The kit is dedicated to the public domain under CC0 1.0, with one exception: the words of the Economic Survey 2020-21 in `examples/es2021_ch6/lines.json` and `examples/es2021_ch6/loci.jsonl` are a publication of the Government of India, reproduced in excerpt (kit v1.4). They are not covered by CC0, and the kit grants no permission to reuse them. The papers it accompanies are licensed separately (the body of *What Breaks in a Citation* under CC BY 4.0).

## Corrections

Corrections are welcome — open an issue. They are published as dated revisions in `CHANGELOG.md`, not silent edits.

*A discipline that is licensed is a discipline that is not adopted.*
