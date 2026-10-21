# The verbatim-extraction instruction (as used on 24 July 2026) — English translation

This is an English translation of the instruction that opened four working threads on 24 July 2026: the work that *What Breaks in a Citation* v1.2 §8-2 calls verbatim extraction "under an instruction forbidding interpretation". The instruction was written and used in Japanese; the original is `extraction_prompt_2026-07-24_ja.md`, and where the two differ, the Japanese governs. The translation keeps the original's structure and its unfilled placeholders. The original marks its headings with 【】 and its placeholders with ［］; both are [ ] here, and ― (U+2015) is —.

In all four threads the "Items to extract" block was left as the unfilled template; the actual items were appended, numbered, after the report table. They are in `examples/extraction_2026-07-24/`.

Note on the paper's wording. §8-2 and the paper's disclosure describe this instruction as one that "forbade summarising, characterising, or judging relevance"; the Japanese edition says 要約・性格づけ・重要性の判断. The instruction itself forbids summarising, paraphrasing and interpreting (要約・言い換え・解釈), and says that judgments of importance and explanations of relations to other provisions are not required (不要). "Characterising" (性格づけ) is not in it, and the instruction speaks of importance (重要性), not relevance. The Japanese edition's §9-5 has a third wording, 要約や重要性の判断を禁じる ("forbidding summary and judgments of importance"). This is entry #66 of the log the author keeps after the paper's v1.2, not yet published.

The revised instruction is `extraction_prompt_v2_en.md`.

```text
From the PDF below, extract the specified provisions "verbatim".
[Must follow]
- Verbatim quotation of the provision only. Add no summary, paraphrase or interpretation whatsoever.
- If there are amendment-history footnotes, copy those verbatim as well (they contain important information).
- If a provision cannot be found, report "not found". Do not fill in by guessing.
- No judgment of importance, and no explanation of relations to other provisions, is needed.
[Handling the PDF]
- First check the page count and whether there is a text layer (pdfinfo / pdffonts).
- If there is no text layer, OCR it (tesseract).
- Always identify the page number of each provision.
[Items to extract]
1. [provision number] — [description in Japanese]
2. [provision number] — [description in Japanese]
[Report format]
Fill in the table below and return it.
| Item | Content |
|---|---|
| Formal title of the source | |
| Issuing body | |
| Edition / date of last amendment | |
| Total pages | |
| Page of the provision | |
| Verbatim quotation | (exactly as in the original) |
| Amendment-history footnotes | (exactly as in the original, if any) |
| Items not found | |
```

CC0 1.0. Part of the citation provenance kit (v1.9).
