# The author's log after the paper's v1.2 (kit v1.8)

`after_v1.2.csv` holds entries #45–#62 of the correction log that the author keeps after *What Breaks in a Citation* v1.2 (the published v1.2 log ends at #42 in English and #44 in Japanese). They are not yet in a published edition of the paper.

Only these columns are kept: the entry number, the date found, "what would have happened had it gone unnoticed", "stakes", who wrote the first of those, the duration and the phase. The other columns (what surfaced, component, how it came to notice, rule, outcome) are left out, as is all text of the entries except the three judgments that were made.

- Three entries (#46–#48) have a judgment, written on 13 October 2026. In each, the assistant (Claude) offered two or three options with a short description, the author chose one by its stakes label, and the description was recorded as the field's text, with "(著者の判断、2026-10-13。Claudeが示した候補から選択)".
- Fifteen entries record the two judgment columns as not yet decided, with the date the entry was made.
- No entry records a duration.

```
python3 tools/catchlog.py examples/series_log/after_v1.2.csv --fields
```
