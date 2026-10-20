# A test where an empty answer can be right (kit v1.6)

`items.jsonl` holds five questions with eleven slots. Six slots have a value as their right answer; five have an empty one: two `not-established`, one `expired`, two `no-record`. The right answer is set against the evidence given with each question, not against the world. `tools/nulleval.py` scores answers into six outcomes plus `unread`, and never into a single score.

The evidence is taken only from material the kit or its papers already hold: the Economic Survey 2020-21 excerpts and dependency records of `examples/es2021_ch6/`, the kit's `register/status_log.jsonl`, and the proviso to Rule 3(1) of the Companies (Accounts) Rules 2014 as *What Your Buyer Is Defending Against* v1.1 quotes and paraphrases it (the official text could not be reached when the test was built). The Economic Survey words are the Government of India's and are **not** CC0, as in `examples/es2021_ch6/`. The `plausible` values used by the "always fill" baseline are deliberately unverified and may be false.

## The run of 20 October 2026 (`runs/2026-10-20/`)

Six fresh agents, each run by Claude in the session that built the kit (configured model `claude-opus-5-5`; the model that actually served a run can differ, and was not recorded), each read only its prompt file and wrote one answer sheet. Three got `prompt_plain.txt`, which asks for answers; three got `prompt_schema.txt`, which adds an `empty` field with the three kinds and a `basis` field, and says "Give a value only if the evidence given establishes it. Do not supply facts from memory."

| Sheet | value-correct | filled | blanked | empty-correct | empty-kind |
| --- | --- | --- | --- | --- | --- |
| schema 1–3 (each) | 6 | 0 | 0 | 5 | 0 |
| plain 1, plain 2 (each, after reading) | 6 | 0 | 0 | 5 | 0 |
| plain 3 (after reading) | 6 | 1 | 0 | 4 | 0 |
| baseline: always fill | 6 | 5 | 0 | 0 | 0 |
| baseline: always empty | 0 | 0 | 6 | 2 | 3 |

The plain answers were prose. Six slots per sheet opened like a refusal and could not be scored without reading them; an agent that had written neither questions nor answers read them and recorded its readings (`readings_plain_*.json`). In plain 3, the answer on which notification brought the proviso into force declined ("Not stated in the evidence") and then supplied one "from memory, not verified here". That is scored as filled.

Five questions and one model are a demonstration of what the scoring catches, not a measurement of the model.

```
python3 tools/nulleval.py evals/null/items.jsonl evals/null/runs/2026-10-20/answers_plain_3.json --readings evals/null/runs/2026-10-20/readings_plain_3.json
```
