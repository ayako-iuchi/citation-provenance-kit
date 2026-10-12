# Changelog

Revisions are dated and kept visible. Nothing is changed silently.

## Unreleased (kit v1.3, in preparation)

- **Found 2026-10-12 — the register disagrees with the post it came from.** The Register in motion row for Japan's National Tax Agency Q&A (kit v1.1 and v1.2) still says that one practitioner report (C) gives a publication date of 10 July 2026, and that question numbers and pages are to be retaken. Hypothetical Technical Blog #17, in its draft as it stands on 12 October 2026, says more: two practitioner reports, dated 13 and 14 July, both give that date; the A grade for "June 2025 edition current on 24 July 2026" is withdrawn; and the citations held (Q7 on printed p. 9, Q55 and Q56 on p. 42, in the July 2026 edition's contents).
- The row is **left as it stands in this release on purpose.** The template keeps one value and one "last resolved" date per row, so correcting the row would also erase the record that the kit once said otherwise. Kit v1.3 will add the newer finding as a new, dated entry and keep the 10 October value beside it.
- Recorded in the method paper's log as entry #46.
- Added `schema/` (snapshot and status assertion), `register/status_log.jsonl`, `register/snapshots.json`, `tools/statuslog.py`, `tools/migrate_register.py` and `tests/test_statuslog.py`. The status log's first five lines are the v1.1 register, converted by `migrate_register.py` without change; the sixth is the finding of 12 October, which names the line it supersedes. The v1.1 register CSV and the workbook sheet are unchanged.
- The one snapshot, Q55 of the National Tax Agency Q&A (June 2025 edition), has `read_on: null`. The day those words were read was not recorded, and is not supplied.
- **Found 2026-10-12 — `CITATION.cff` still gives version 1.1.1.** Kit v1.2 did not update it. To be corrected at the v1.3 release, not before, so that the released file and the version it names agree. Recorded in the method paper's log as entry #47.

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
