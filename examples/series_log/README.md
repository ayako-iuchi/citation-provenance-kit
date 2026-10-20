# The author's log after the paper's v1.2 (kit v1.8)

`after_v1.2.csv` holds entries #45–#62 of the correction log that the author keeps after *What Breaks in a Citation* v1.2 (the published v1.2 log ends at #42 in English and #44 in Japanese). They are not yet in a published edition of the paper.

Only these columns are kept: the entry number, the date found, "what would have happened had it gone unnoticed", "stakes", the duration and the phase, as recorded. The column "Who wrote 'what would have happened'?" is not in the source; it is derived here, from the note on #46–#48 and as "not yet decided" for the rest. The other columns (what surfaced, component, how it came to notice, rule operating, whether an existing rule fired, outcome) are left out, as is all text of the entries except the three judgments that were made.

- Three entries (#46–#48) have a judgment, each ending "（著者の判断、2026-10-13。Claudeが示した候補から選択）" (the author's judgment, 13 October 2026; chosen from options Claude offered).
- Fifteen entries record the two judgment columns as not yet decided, with the date the entry was made.
- No entry records a duration.

```
python3 tools/catchlog.py examples/series_log/after_v1.2.csv --fields
```
