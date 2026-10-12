# Citation provenance kit

Reproduction kit for **What Breaks in a Citation** (v1.1, 26 July 2026) by Ayako Iuchi.
Kit v1.1 · **CC0 1.0** — no rights reserved. Copy, change and use it without asking or attributing.

The paper argues that machine-assisted writing breaks less often in *what a source says* than in *what is true of the source*: its date, edition, page, identifier, or whether it is in force. This kit is the set of working materials for keeping that record while you write.

## What is in it

| Path | What it is |
| --- | --- |
| [`kit/citation-provenance-kit.xlsx`](kit/citation-provenance-kit.xlsx) | The kit in one workbook: catch log, components, grades & notation, cost calculator, and the paper's own 25-entry log as a worked example |
| [`csv/catch_log_template.csv`](csv/catch_log_template.csv) | The catch log columns and one example row, for any tool |
| [`csv/components.csv`](csv/components.csv) | The ten components, a definition each, and the sorting question |
| [`csv/example_log_v1.1.csv`](csv/example_log_v1.1.csv) | Appendix A-2 of the paper (v1.1), lightly condensed |
| [`csv/register_in_motion_template.csv`](csv/register_in_motion_template.csv) | Register of provisions in motion: status components, the issuer's source, last resolved, next check, and known pending changes (kit v1.1) |
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

## What this kit does not do

It verifies nothing. It records what your verification acts produced. A document can be perfectly graded and still misread.

## Sources

- What Breaks in a Citation — [English](https://lnkd.in/p/giTfeMUh) · [日本語](https://lnkd.in/p/gFUXFv2w)
- What Your Buyer Is Defending Against (the source project) — [English](https://lnkd.in/p/gHNjBuCd) · [日本語](https://lnkd.in/p/gF-kd9DF)

The example log is the author's English translation. The original log was kept in Japanese and governs; from v1.2 of the paper (12 October 2026) it is published as Appendix A-2 of the Japanese edition. In v1.1 it was referenced but not published. Its component and rule columns are the author's classification, applied afterwards (grade D). Four entries are contested; see the paper, Appendix A-4.

## Licence

The kit is dedicated to the public domain under CC0 1.0. The papers it accompanies are licensed separately (the body of *What Breaks in a Citation* under CC BY 4.0).

## Corrections

Corrections are welcome — open an issue. They are published as dated revisions in `CHANGELOG.md`, not silent edits.

*A discipline that is licensed is a discipline that is not adopted.*
