# Changelog

Revisions are dated and kept visible. Nothing is changed silently.

## Kit v1.6 — unreleased

- Added `tools/nulleval.py`, `schema/null_item.schema.json`, `evals/null/` (five questions, eleven slots, and the run of 20 October 2026) and `tests/test_nulleval.py`. Standard library only, as before. The test's Economic Survey excerpts are the Government of India's and are not CC0.
- **Found 2026-10-20 — the first scorer misread polite refusals.** Its first version counted prose such as "Not stated in the evidence…" as a value, so the three plain-prompt runs scored as filling every empty slot. Prose that opens like a refusal is now scored `unread` until a reader records what it does, in a readings file that names its reader. The stored results are those after reading.
- The official text of the proviso to Rule 3(1) of the Companies (Accounts) Rules 2014 could not be reached from the government sites on 20 October 2026. The test uses the wording as *What Your Buyer Is Defending Against* v1.1 quotes and paraphrases it, and its label says so.

## README update — 2026-10-20 (no new version)

- Both READMEs list Hypothetical Technical Blog #23, *The Component Is the Type* (published in English on note and LinkedIn on 20 October 2026, after kit v1.5 was released), among the posts that use the kit, and say that it names the version it describes. No other file changed.

## Kit v1.5 — 2026-10-20

- **Released on 20 October 2026,** before Hypothetical Technical Blog #23 (*The Component Is the Type*), which cites it, is published. `main` was fast-forwarded to the branch `kit-v1.5`; no history was rewritten. The entries below were written while the release was in preparation and are kept as written.
- Known issue: `citelint.py` reads inside Markdown inline code, and with `--lang ja` it reports check C5 on `[Note: B]` written as inline code in the Japanese edition of #23; with `--lang en` it does not. A false positive, to be fixed in a later version. `notation.py --markdown` skips code.

- Added `tools/notation.py`, `schema/annotation.schema.json`, `examples/method_paper_v1.2/` and `tests/test_notation.py`. The notation is read as typed records, in English and Japanese with one grammar, and checked for its form (N0–N7). Standard library only, as before. N0 (a bracket that names a component but does not follow the grammar), N5 (a component twice) and N7 (a first slot that is not established, reported as a notice) are not rules of the paper; they are added here. Extension components (§4-2) are declared with `--extend`.
- A separate agent reviewed the first draft (c5d12de) on 20 October 2026. It read Markdown links such as `[A](url)` as annotations and broke them when rewriting, passed malformed annotations in silence, read prose such as `[Note: B]` as an annotation, read inside code, and changed CRLF line endings. Each is fixed and has a test. A second review of the fixes (15c6fb6) found that the link check dropped annotations followed by a footnote or a parenthesis, that an unmatched backtick hid the rest of a document under `--markdown`, that fences did not close as CommonMark closes them, and that a page number in brackets after a component name was reported as an error; these too are fixed and tested.
- **Found 2026-10-20 — the kit's closed vocabulary was two lists.** From kit v1.0 to v1.4, `csv/components.csv` and the workbook's Components sheet gave the Japanese name of *wording* as 文言. The paper's Japanese edition (§4-2, and its three annotations that use it) and `citelint.py` (from v1.2) give 語. Found when `notation.py`, which reads the vocabulary from `components.csv`, rejected the paper's own ［語: A｜頁: —］. Recorded as entry #57 of the method paper's log, which the author keeps after v1.2 (the published v1.2 log ends at #42 in English and #44 in Japanese); not yet published. Corrected to 語 in `tools/build_kit.py`, `csv/components.csv` and the workbook. The workbook was regenerated and saved again through LibreOffice, as before; compared with v1.4 cell by cell, values and cached results, the one change is Components!B5. Row heights and data validations are unchanged. A test now checks that `build_kit.py`, `components.csv` and `citelint.py` hold the same vocabulary.

## README update — 2026-10-20 (no new version)

- Both READMEs list Hypothetical Technical Blog #22, *The Chunk Is the Citation* (published on note on 20 October 2026, after kit v1.4 was released), among the posts that use the kit, and say that #22 names the version it describes. No file other than the READMEs and this one changed.

## Kit v1.4 — 2026-10-20

- **Released on 20 October 2026,** before Hypothetical Technical Blog #22 (*The Chunk Is the Citation*), which cites it, is published: the order #20 and v1.3 got wrong. `main` was fast-forwarded to the branch `kit-v1.4`; no history was rewritten. The entries below were written while the release was in preparation and are kept as written.
- Known issue: `citelint.py --lang ja` reports check C5 (notation outside the vocabulary) on a JSON code block in the Japanese edition of #22, which uses no grade notation there. A false positive, to be fixed in a later version.

- Added `tools/pdflines.py`, `tools/loci.py`, `tools/retrieve.py`, `tools/depaudit.py`, `schema/locus.schema.json`, `schema/dependency.schema.json`, `examples/es2021_ch6/` and `tests/test_loci.py`, `tests/test_depaudit.py`. Standard library only, as before.
- `register/status_log.jsonl` gains one line, `2026-10-20-01`: the World Bank's Doing Business report, discontinued (announced 16 September 2021). No expiry is stated, so a query reports `no-expiry-stated`. The earlier lines are unchanged (`statuslog.py --verify-append` against v1.3 says yes).
- The example's chapter words are the Government of India's, reproduced in excerpt. They are not covered by the kit's CC0 dedication; `examples/es2021_ch6/README.md` says so.
- Found while building the example, 2026-10-20: in the chapter, footnote 6 (attached to ¶6.20) is printed at the foot of p. 188, in the middle of ¶6.22; ¶6.22 runs across pp. 188–189; and ¶6.32 and ¶6.27 print "Buisness". Each is now a test.
- The dependency records were drafted by Claude at the author's direction and were not reviewed by the author, who on 20 October 2026 chose to accept Claude's judgement; `recorded_by` says so. A separate agent checked them against the printed pages on 20 October 2026, and the records were corrected before release (quotations completed, one record added for the source of Figures 1 and 2, one interpretation stated in a note).
- `loci.py` recognises paragraphs, lettered headings and footnotes only. On whole pages it appends tables, figures and source lines to the paragraph before them, so the example runs on lines excerpted by hand. Its docstring says so.
- `register/status_log.jsonl`'s new line was reworded before release (the World Bank Group's own words; `next_check` "None set"). The v1.3 lines are untouched.
- The README and `CITATION.cff` state that the example's chapter words are not CC0.

## Kit v1.3 — 2026-10-20

- **Released on 20 October 2026.** `main` was fast-forwarded to the branch `kit-v1.3`; no history was rewritten. The entries below were written while the release was in preparation and are kept as written, except where marked.
- **Found 2026-10-20 — a post cited this release before it existed.** Hypothetical Technical Blog #20, *Fixed Words, Moving Status*, was published on note on 13 October 2026 (14:40 JST). Its sources list "Citation provenance kit, v1.3" and link to this repository, whose default branch then held v1.2. For seven days the branch that link opens on did not hold v1.3; the work sat on the branch `kit-v1.3`.
- **Found 2026-10-20 — no release had a tag.** v1.0 to v1.2 were named only in this file and in the README. Tags were added on 20 October 2026 at the commits that made each release: `v1.0` 02de134, `v1.1` 3c93219, `v1.1.1` fc5a27b, `v1.2` b55e308. They mark the release commits; they were not there at the time. `v1.3` marks this release.
- `CITATION.cff` now gives version 1.3, released 2026-10-20 (entry #47 below).
- The READMEs no longer mark the status log files "unreleased", list the posts that use the kit, and name the release tags.

- **Found 2026-10-12 — the register disagrees with the post it came from.** The Register in motion row for Japan's National Tax Agency Q&A (kit v1.1 and v1.2) still says that one practitioner report (C) gives a publication date of 10 July 2026, and that question numbers and pages are to be retaken. Hypothetical Technical Blog #18, *Commencement Is a Cache-Invalidation Problem*, in its draft as it stands on 12 October 2026, says more: two practitioner reports, dated 13 and 14 July, both give that date; the A grade for "June 2025 edition current on 24 July 2026" is withdrawn; and the citations held (Q7 on printed p. 9, Q55 and Q56 on p. 42, in the July 2026 edition's contents).
- The row is **left as it stands in this release on purpose.** The template keeps one value and one "last resolved" date per row, so correcting the row would also erase the record that the kit once said otherwise. Kit v1.3 will add the newer finding as a new, dated entry and keep the 10 October value beside it.
- Recorded in the method paper's log as entry #46.
- **2026-10-13 — the blog posts were renumbered.** An earlier series reached #16, so the posts of this series moved up by one: #16–#19 became #17–#20. Blog numbers in the kit now name the post by number and title. Log entry numbers (#1–#48, as in `csv/components.csv` and the worked example) are a different series and did not change.
- **Found 2026-10-13 — the released README names the linter post by a number that now belongs to another post.** Kit v1.2 says "Hypothetical Technical Blog #18 reports the run". After the renumbering, #18 is *Commencement Is a Cache-Invalidation Problem*; the run is reported in #19, *A Rule Is Not a Mechanism*. Corrected on the released branch on 13 October (see the README correction below); v1.3 also gives the post's title. Recorded in the method paper's log as entry #48.
- Line 6 of `register/status_log.jsonl` is not yet released. Its source now gives the post's new number and its title. This is a correction to an unreleased draft, kept visible in the Git history, not an edit to a released line.
- Added `schema/` (snapshot and status assertion), `register/status_log.jsonl`, `register/snapshots.json`, `tools/statuslog.py`, `tools/migrate_register.py` and `tests/test_statuslog.py`. The status log's first five lines are the v1.1 register, converted by `migrate_register.py` without change; the sixth is the finding of 12 October, which names the line it supersedes. The v1.1 register CSV and the workbook sheet are unchanged.
- The one snapshot, Q55 of the National Tax Agency Q&A (June 2025 edition), has `read_on: null`. The day those words were read was not recorded, and is not supplied.
- **Found 2026-10-12 — `CITATION.cff` still gives version 1.1.1.** Kit v1.2 did not update it. To be corrected at the v1.3 release, not before, so that the released file and the version it names agree. Recorded in the method paper's log as entry #47.

## README correction — 2026-10-13 (no new version)

- The blog posts of this series were renumbered: an earlier series reached #16, so #16–#19 became #17–#20. Kit v1.2's README said "Hypothetical Technical Blog #18 reports the run"; after the renumbering, #18 is *Commencement Is a Cache-Invalidation Problem*. The run is reported in #19, *A Rule Is Not a Mechanism*. Both READMEs were corrected on 13 October 2026 (commit c9a9823). That commit did not record the change here; this entry does. Recorded in the method paper's log as entry #48.

## Kit v1.2 — 2026-10-12

- Added `tools/citelint.py`, a linter with six checks (C1–C6), its tests, and its output on both editions of the paper in `evidence/`.
- Run on v1.1, it reports post-release entries #27, #29, #30, #31, #41, #42, #43 and #44, and the shape of #36. It does not report #26, #28, #32, #33, #35 or #37–#40.
- It also reports one defect no reader had found: the Japanese edition's Contents gives chapter 3 as 「検証の単位は結合であって、主張ではない」, while the heading reads 「検証の単位は、主張ではなく結合である」. Present in v1.1 and v1.2.
- The v1.2 files checked are the author's build files of 12 October 2026. The editions as published may differ in layout.

## Kit v1.1.1 — 2026-10-12

- README and the example-log sheet now say where the governing Japanese log is published (Appendix A-2 of the Japanese edition, from paper v1.2). Kit v1.0 and v1.1 said the Japanese original governs without saying it was unpublished; that statement came from the paper and is corrected there as entry #36.

## Kit v1.1 — 2026-10-10

- Added the **Register in motion** sheet and `csv/register_in_motion_template.csv`: one row per status component (commencement, edition, existence, dependency), with the issuer's source, the date last resolved, the next check, and known pending changes that could move the value.
- Example rows are the domain paper's own register, re-resolved on 10 October 2026. Two rows carry an unresolved conflict and are marked with the null slot rather than filled.

## Kit v1.0 — 2026-10-10

- First public release, accompanying *What Breaks in a Citation* v1.1 (26 July 2026).
- Workbook: catch log, components, grades & notation, cost calculator, worked example (Appendix A-2, lightly condensed).
- The catch log adds four columns the paper's original log lacked: date found, whether an existing rule fired (§9-1), stakes (§7-1) and phase (§9-7).
- Component definitions and the "can it become false without the document changing?" assignments are drafted for this kit; the paper names the components but does not define them.
