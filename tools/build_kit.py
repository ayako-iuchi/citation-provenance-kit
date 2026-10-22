"""Build the reproduction kit for 'What Breaks in a Citation' (v1.1). CC0 1.0."""
import csv
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.comments import Comment
from openpyxl.worksheet.datavalidation import DataValidation

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

KIT_VERSION = "1.11"
PAPER = "What Breaks in a Citation, v1.1 (26 July 2026); files made from v1.2 (12 October 2026) name it"

F = "Arial"
HDR_FILL = PatternFill("solid", fgColor="1F2933")
INPUT_FILL = PatternFill("solid", fgColor="FFF9C4")
EX_FILL = PatternFill("solid", fgColor="F3F4F6")
THIN = Side(style="thin", color="CBD2D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")


def header(ws, row, labels, widths):
    for i, (lab, w) in enumerate(zip(labels, widths), start=1):
        c = ws.cell(row=row, column=i, value=lab)
        c.font = Font(name=F, bold=True, color="FFFFFF", size=10)
        c.fill = HDR_FILL
        c.alignment = Alignment(wrap_text=True, vertical="center")
        c.border = BORDER
        ws.column_dimensions[c.column_letter].width = w
    ws.row_dimensions[row].height = 34


def body(cell, bold=False, color="000000", fill=None):
    cell.font = Font(name=F, size=10, bold=bold, color=color)
    cell.alignment = WRAP
    cell.border = BORDER
    if fill:
        cell.fill = fill


def title(ws, text, sub):
    ws["A1"] = text
    ws["A1"].font = Font(name=F, size=14, bold=True)
    ws["A2"] = sub
    ws["A2"].font = Font(name=F, size=10, italic=True, color="52606D")


# ---------------------------------------------------------------- data
COMPONENTS = [
    # name, ja, definition, can become false without the document changing?, example from the source project
    ("wording", "語", "The words the claim attributes to the source are the words in it.", "No",
     "A rule cited as listing 'life cycle cost' among its criteria; the phrase was not in it (#8)."),
    ("figure", "数値", "A quantity stated or derived from the source is correct.", "No (derived values: see Grades sheet)",
     "A 1.6% ratio derived from two cited primary values; never examined in v1.1."),
    ("page", "頁", "The locator (printed page, paragraph, article) points to where the text is.", "No",
     "Printed numbering ran three behind the file numbering in a 177-page instrument."),
    ("date", "日付", "A date attributed to the source or computed from it is correct.", "No",
     "'Eighteen months from publication' rendered as a specific day (#11)."),
    ("edition", "版", "The edition, vintage or version cited is identified, current where currency matters, and not mixed.", "Yes",
     "Two vintages of an official translation in circulation (#5); the change-marked edition cited as authoritative (#23)."),
    ("identifier", "識別子", "The identifier resolves to the one instrument intended, not a namesake.", "No",
     "G.S.R. 206(E) of 2015 and of 2021 (#22)."),
    ("existence", "存在", "The cited provision or document exists in the version relied on.", "Yes",
     "A supplementary principle deleted in a code revision (#14); a memorandum absent from the consolidated rules (#9)."),
    ("commencement", "施行", "The provision is in force on the date the text speaks from.", "Yes",
     "An obligation described in the present tense, eighteen months before commencement (#18, recurred #24)."),
    ("attribution", "帰属", "The statement is attributed to the body that actually made it.", "No",
     "Guidance from a professional institute treated as if it settled a statutory question (#17)."),
    ("dependency", "依存", "What the source itself rests on still holds (not withdrawn, retracted or discredited).", "Yes",
     "A government chapter drawing, at two paragraphs, on a discontinued index (§6-2)."),
]

GRADES = [
    ("A", "Verified directly against the primary source for that component", "一次資料で直接確認"),
    ("B", "Peer-reviewed research, an international body, or a professional institute's published analysis", "査読研究・国際機関・専門職団体の公表分析"),
    ("C", "Industry survey, general reporting, or practitioner commentary", "業界調査・一般報道・実務家の論評"),
    ("D", "The author's own assessment, always stated as such", "著者自身の評価（常にそう明示）"),
    ("—", "Not established; this document does not assert it (the null slot)", "確定しておらず、本文は主張しない（ヌルスロット）"),
]

NOTATION_RULES = [
    ("Form", "[component: grade | component: grade]  e.g. [wording: A | commencement: —]. Japanese: ［語: A｜施行: —］ — same shape in every language."),
    ("Grade the source, not your confidence", "A grade reports the character of the source for that component. A reader must be able to overturn it by opening the source."),
    ("First slot = load-bearing", "The first slot is the component the claim rests on. If you cannot name it, the claim is not precise enough to cite."),
    ("Mark, never omit", "Where a load-bearing component cannot be established, write the em dash. An omitted slot is indistinguishable from one never considered."),
    ("Only where grades diverge", "If all components carry the same grade, write a plain [A]. Do not split where the divergence is not load-bearing."),
    ("Three slots maximum", "Needing a fourth means one sentence carries several claims. Split the claim, not the citation."),
    ("Close the vocabulary", "Declare every component and grade token in the document that uses it. An undefined token reached publication in the source project (§7-4)."),
    ("Derived values (provisional, untested)", "A value computed from cited primaries is neither A nor D. The paper proposes a marker but has not tested one (§4-6, §9-3). Suggested interim: grade the operands, and state the arithmetic beside it, labelled as the author's."),
]

COST_ACTIONS = [
    ("Verbatim confirmation at the printed page", "逐語確認（印字頁）"),
    ("Edition pinning", "版の固定"),
    ("Identifier disambiguation (triple key)", "識別子の特定（三点キー）"),
    ("Obtaining consolidated text", "統合テキストの入手"),
    ("Tracing a revision / amendment chain", "改正の連鎖の追跡"),
    ("Dependency audit (paragraph level)", "依存監査（段落単位）"),
    ("Log entry", "ログ記入"),
    ("Rework (rewriting already-drafted text)", "手戻り（書き上げた本文の書き直し）"),
]

# Appendix A-2 of the paper (v1.1). Error → correction and manner of discovery are grade A (contemporaneous);
# component and rule attribution are grade D (applied afterwards). Translated from the Japanese original log.
EXAMPLE = [
    (1, "A practice generated the institutions → the institutions still make the practice rational (the practice is older)", "Self-review", "outside", "—", ""),
    (2, "A national audit body was the counterpart to a ministry report → the counterpart is a paragraph of a government economic survey; the audit body's remit does not reach private firms", "Primary source check", "attribution", "—", ""),
    (3, "An official translation omitted \"such as\" → both vintages contain it", "Official translation PDF", "wording", "Translation policy", ""),
    (4, "\"borrowing in a large amount\" → \"in a significant amount\"", "Official translation PDF", "wording", "Translation policy", ""),
    (5, "\"transfer is wrong, assignment is right\" → the framing was wrong: two vintages of the official translation circulate; citing without specifying which is the error", "Comparison of both files", "edition", "Pin the edition", ""),
    (6, "Applicability by market capitalisation → the capitalisation wording was deleted from the regulation on a stated date", "Consolidated regulation", "edition", "Register of provisions in motion", ""),
    (7, "The committee's terms of reference required amendment → the scope is mandated by a schedule; no amendment needed", "Consolidated regulation", "wording", "—", "Contested (§A-4)"),
    (8, "A procurement rule listed \"life cycle cost\" among its criteria → the phrase is not in the rule; a secondary gloss had been promoted to statutory text; price is one of five criteria and one had been dropped", "Primary source at printed page", "wording + dependency", "Verbatim at the printed page", ""),
    (9, "The basis for quality-and-cost selection was a 2021 office memorandum → the memorandum is not in the consolidated rules; the basis is a numbered rule in the main text", "Full-text search of consolidated rules", "identifier + existence", "—", ""),
    (10, "An e-marketplace obligation bound procuring entities generally → it binds ministries and departments", "Primary source", "wording", "—", ""),
    (11, "Substantive commencement on a specific day → commencement is expressed as an interval; state the month, do not compute the day", "Gazette notification", "date", "Quote the period, do not compute the date", ""),
    (12, "A proposed name for a fictional entity → rejected; the prefix belongs to public-sector naming convention", "Reconsideration of reader assumptions", "outside", "—", ""),
    (13, "The 2021 edition of a governance code was current → it was revised and took effect three days before the paper's date", "Primary source", "edition", "Register of provisions in motion", ""),
    (14, "A supplementary principle requiring disclosure of delegated authority was current → deleted in the revision", "Code text", "existence", "Register of provisions in motion", ""),
    (15, "A supplementary principle on risk management → promoted to a principle, with specifics moved to guidance outside comply-or-explain", "Code text", "edition", "Register of provisions in motion", ""),
    (16, "The rules permit quality-weighted selection, so lowest-price is practice not rule → the quality-weighted route is confined to consultancy; software falls under goods; the goods rule directs award to the lowest evaluated bidder; non-financial weighting is capped", "Cross-reading four provisions", "wording", "Mechanism over content", "Contested (§A-4) — strongest candidate"),
    (17, "A vendor's third-party certification satisfies the audit-trail requirement → it does not on its own; the assurance report must address the statutory requirement and cover the buyer's reporting period", "Professional institute guidance", "attribution", "—", "Contested (§A-4)"),
    (18, "A statutory provision means liability does not transfer (present tense) → not yet in force; commencement eighteen months out", "Gazette commencement order", "commencement", "Do not write an unenforced obligation in the present tense", ""),
    (19, "The doctrine is unestablished / does not reach the forum → both diverge from the source: it exists, is not codified in the same language, and there is apprehension that it is not taken into account", "Source text", "wording", "Do not characterise from memory / Do not drop the qualifiers", ""),
    (20, "The statutory list of reserved matters is closed → it is not; a residual clause permits extension by rules; extension is prospective, published and dated", "Statute at printed page", "wording", "Do not characterise from memory", "Contested (§A-4)"),
    (21, "An annually revised government Q&A: the 2022 edition was current → the 2025 edition is current; a cited rule renumbers on a stated future date", "Issuing authority's site", "edition + date", "Register of provisions in motion", ""),
    (22, "A rule adds nine items to the statutory list (unamended) → the rule has been amended; nine notifications over five years, chain open; the G.S.R. 206(E) collision was found inside this chain", "Chain trace", "edition → identifier", "Cite consolidated text only / Triple-key identification", ""),
    (23, "The authoritative file of the Q&A is one PDF → that file is the change-marked edition; page references must be retaken", "Issuing authority's site", "edition", "Pin the edition (second occurrence)", "Recurrence after rule existed"),
    (24, "A control is grounded on a data-protection rule (present tense) → that rule is also eighteen months out; recurrence of #18", "Consolidation pass over the control document", "commencement", "#18's rule, which did not fire", "Recurrence after rule existed"),
    (25, "Permission to name a third party had been obtained → oral only; nothing in writing", "Internal contradiction in the control document", "outside", "—", ""),
]

OUTCOMES = ["corrected", "deleted", "weakened", "excluded", "abstained", "slipped", "confirmed (no error found)"]
STAKES = ["A step of the argument collapses", "A claim must be weakened", "One footnote dies", "No effect on the argument"]
FIRED = ["Yes — the rule caught it", "No — rule existed but did not fire", "No rule existed yet"]
PHASE = ["Pre-release", "Post-release"]
WHO = ["author", "author chose from assistant's options", "assistant", "not yet decided"]

CATCH_COLS = [
    ("#", 6),
    ("Date found\n発見日", 12),
    ("What surfaced\n何が表に出たか", 40),
    ("Component(s)\n成分", 16),
    ("How it came to notice\nどう気づいたか", 24),
    ("Rule operating (if any)\n働いていた規則", 24),
    ("Did an existing rule fire?\n既存の規則は発火したか", 22),
    ("Outcome\n結果", 18),
    ("What would have happened had it gone unnoticed\n見逃していたら何が起きたか", 40),
    ("Stakes\n影響の大きさ", 24),
    ("Who wrote 'what would have happened'?\n「見逃していたら」を誰が書いたか", 22),
    ("Duration (minutes)\n所要時間（分）", 12),
    ("Phase\n公開前／後", 14),
]

CATCH_EXAMPLE = [
    "Ex.", "(YYYY-MM-DD)",
    "A procurement rule was cited as listing \"life cycle cost\" among its criteria. The phrase is not in the rule; a secondary summary's gloss had been promoted to statutory text.",
    "wording", "Opened the primary source at the printed page", "(none — this failure produced the rule)",
    "No rule existed yet", "corrected",
    "The comparison of evaluation criteria would have rested on words the regulator never wrote.",
    "A step of the argument collapses", "", "", "Pre-release",
]

# ---------------------------------------------------------------- workbook
wb = Workbook()

# README sheet
ws = wb.active
ws.title = "Start here"
title(ws, "Citation provenance kit — reproduction kit", f"Kit v{KIT_VERSION} · accompanies {PAPER} · CC0 1.0 (no rights reserved)")
lines = [
    ("What this is", "The working materials for the discipline described in What Breaks in a Citation: a catch log, a closed list of citation components, the grading and notation rules, a cost calculator, and the author's own 25-entry log (lightly condensed) as a worked example. The Note column on recurrences is added by the kit."),
    ("Where to type", "Yellow cells are inputs. Grey rows are examples — overwrite or delete them. Everything else is reference or formula."),
    ("Sheets", "Catch log — your record, one row per catch, confirmation or abstention.\nComponents — the ten components and the one sorting question.\nGrades & notation — A–D, the null slot, and the rules for writing them.\nCost calculator — actions × counts × your own unit times.\nExample log v1.1 — Appendix A of the paper, lightly condensed.\nRegister in motion — status components with an issuer\'s source and a next-check date (kit v1.1)."),
    ("Three rules for the log", "1. Record confirmations and abstentions, not only corrections. Without them there is no denominator.\n2. Fill the 'what would have happened' column yourself. It is the one field nobody else can fill. If an assistant drafted it, or you chose from its options, say so in the 'Who wrote' column (kit v1.8).\n3. Keep the log open after release. Publication is a marker in the log, not its end."),
    ("Columns the original log lacked", "Besides its numbering, the original log kept three things for each entry: what was wrong, what was right, and how it came to notice (Appendix A-0). The component and rule columns were added afterwards, at grade D. The paper says the six fields of §7-1 were recorded for each correction, and §8-1 that the corrections were logged with their component, rule and consequence; the published log (Appendix A-2, and A-6 in paper v1.2) shows no 'what would have happened' column.\n'Did an existing rule fire?': two rules failed to prevent their own failure from recurring, and the log could not show it (Appendix B, §9-1).\n'Duration': no effort was recorded and it cannot be reconstructed (§8-1).\n'Stakes': the distinction between a step of the argument collapsing and one footnote dying (§7-1), as a filterable field.\n'Phase': the log closed at release, so post-publication defects went unnumbered (§9-7).\n'Who wrote what would have happened?': the field cannot be delegated (§9-5), so record when it was drafted by an assistant or chosen from an assistant's options (kit v1.8)."),
    ("What this kit does not do", "It does not verify anything. It records what your verification acts produced. A perfectly graded document can still be misread."),
    ("Licence", "CC0 1.0 Universal. Copy, modify and use it for any purpose without asking or attributing. https://creativecommons.org/publicdomain/zero/1.0/"),
    ("Source papers", "What Breaks in a Citation — links listed since kit v1.0: (EN) https://lnkd.in/p/giTfeMUh · (JA) https://lnkd.in/p/gFUXFv2w; v1.2, as cited in Hypothetical Technical Blog #28: (EN) https://lnkd.in/p/gjQ2RAPW · (JA) https://lnkd.in/p/gW5xwpFK\nWhat Your Buyer Is Defending Against (EN) https://lnkd.in/p/gHNjBuCd · (JA) https://lnkd.in/p/gF-kd9DF"),
]
r = 4
for k, v in lines:
    a = ws.cell(row=r, column=1, value=k); body(a, bold=True)
    b = ws.cell(row=r, column=2, value=v); body(b)
    ws.row_dimensions[r].height = max(30, 15 * (v.count("\n") + 1 + len(v) // 95))
    r += 1
ws.column_dimensions["A"].width = 26
ws.column_dimensions["B"].width = 100

# Catch log
cl = wb.create_sheet("Catch log")
title(cl, "Catch log", "One row per correction, confirmation or abstention. The seven fields of §10-4, and five more: date found, whether an existing rule fired, stakes (the distinction of §7-1), who wrote the 'what would have happened' field (§9-5), and phase (§9-7).")
header(cl, 4, [c for c, _ in CATCH_COLS], [w for _, w in CATCH_COLS])
for j, v in enumerate(CATCH_EXAMPLE, start=1):
    body(cl.cell(row=5, column=j, value=v), fill=EX_FILL, color="52606D")
cl.cell(row=5, column=1).comment = Comment("Example row drawn from entry #8 of the paper's log. Overwrite or delete it.", "kit")
N_ROWS = 200
for rr in range(6, 6 + N_ROWS):
    cl.cell(row=rr, column=1, value=rr - 5)
    body(cl.cell(row=rr, column=1))
    for j in range(2, len(CATCH_COLS) + 1):
        body(cl.cell(row=rr, column=j), fill=INPUT_FILL)
cl.freeze_panes = "C5"


def dv_list(ws, items_ref, col, explicit=True):
    if explicit:
        dv = DataValidation(type="list", formula1='"' + ",".join(items_ref) + '"', allow_blank=True)
    else:
        dv = DataValidation(type="list", formula1=items_ref, allow_blank=True)
    dv.showErrorMessage = False  # allow domain-specific values
    ws.add_data_validation(dv)
    dv.add(f"{col}5:{col}{5 + N_ROWS}")


dv_list(cl, "=Components!$A$5:$A$20", "D", explicit=False)
dv_list(cl, [f.replace(",", "") for f in FIRED], "G")
dv_list(cl, OUTCOMES, "H")
dv_list(cl, STAKES, "J")
dv_list(cl, WHO, "K")
dv_list(cl, PHASE, "M")
dvn = DataValidation(type="whole", operator="greaterThanOrEqual", formula1="0", allow_blank=True)
cl.add_data_validation(dvn); dvn.add(f"L5:L{5 + N_ROWS}")

# Components
cp = wb.create_sheet("Components")
title(cp, "Components — a closed list", "Start from these ten. Delete what does not apply, add what your domain needs (rows 15–20), and define every one.")
header(cp, 4, ["Component", "成分", "Definition (drafted for this kit)", "Can it become false without the document changing?\n文書が変わらなくても偽になりうるか",
               "Example from the source project"], [16, 10, 52, 30, 60])
for i, (n, ja, d, s, ex) in enumerate(COMPONENTS, start=5):
    for j, v in enumerate([n, ja, d, s, ex], start=1):
        body(cp.cell(row=i, column=j, value=v), bold=(j == 1))
ext = [("retraction-status", "撤回状態", "Example domain extension (medicine): the cited paper has not been retracted.", "Yes", "—"),
       ("restatement-status", "修正再表示", "Example domain extension (financial reporting): the cited figure has not been restated.", "Yes", "—")]
for i, row in enumerate(ext, start=15):
    for j, v in enumerate(row, start=1):
        body(cp.cell(row=i, column=j, value=v), fill=EX_FILL, color="52606D")
for i in range(17, 21):
    for j in range(1, 6):
        body(cp.cell(row=i, column=j), fill=INPUT_FILL)
cp.cell(row=22, column=1, value="The sorting question (§10-1, §10-5): components marked 'Yes' must be re-resolved from the authoritative register when you write — never recalled, by you or by a model. "
        "The Yes/No assignments for the ten are the kit's suggestion for legal and regulatory sources; check them for your domain.")
cp.cell(row=22, column=1).font = Font(name=F, size=10, italic=True)
cp.merge_cells("A22:E22"); cp.cell(row=22, column=1).alignment = WRAP; cp.row_dimensions[22].height = 32
cp.freeze_panes = "A5"

# Grades & notation
gr = wb.create_sheet("Grades & notation")
title(gr, "Grades & notation", "A grade describes the source for one component. It does not describe the author's confidence.")
header(gr, 4, ["Grade", "Meaning", "意味"], [10, 80, 50])
for i, (g, en, ja) in enumerate(GRADES, start=5):
    for j, v in enumerate([g, en, ja], start=1):
        body(gr.cell(row=i, column=j, value=v), bold=(j == 1))
header(gr, 11, ["Rule", "How to apply it", ""], [10, 80, 50])
gr.column_dimensions["A"].width = 30
for i, (k, v) in enumerate(NOTATION_RULES, start=12):
    body(gr.cell(row=i, column=1, value=k), bold=True)
    c = gr.cell(row=i, column=2, value=v); body(c)
    gr.merge_cells(start_row=i, start_column=2, end_row=i, end_column=3)
    gr.row_dimensions[i].height = 32

# Cost calculator
cc = wb.create_sheet("Cost calculator")
title(cc, "Cost calculator — a method, not a number",
      "Hours = count × unit minutes ÷ 60. Counts and unit times are yours. Any result is grade D and must be labelled so wherever it appears (§8-3).")
header(cc, 4, ["Action", "作業", "Count\n件数", "Unit time (minutes)\n単位時間（分）", "Hours\n時間"], [44, 30, 12, 20, 12])
first = 5
for i, (en, ja) in enumerate(COST_ACTIONS, start=first):
    body(cc.cell(row=i, column=1, value=en)); body(cc.cell(row=i, column=2, value=ja))
    for col in (3, 4):
        c = cc.cell(row=i, column=col); body(c, color="0000FF", fill=INPUT_FILL)
    h = cc.cell(row=i, column=5, value=f'=IF(OR(C{i}="",D{i}=""),"",C{i}*D{i}/60)')
    body(h); h.number_format = "0.0"
last = first + len(COST_ACTIONS) - 1
t = last + 1
body(cc.cell(row=t, column=1, value="Total (grade D)"), bold=True)
body(cc.cell(row=t, column=2, value="合計（D評価）"), bold=True)
tc = cc.cell(row=t, column=3, value=f"=SUM(C{first}:C{last})"); body(tc, bold=True)
th = cc.cell(row=t, column=5, value=f"=SUM(E{first}:E{last})"); body(th, bold=True); th.number_format = "0.0"
body(cc.cell(row=t + 1, column=1, value="Rework share of hours (grade D)"), bold=True)
rs = cc.cell(row=t + 1, column=5, value=f'=IF(E{t}=0,"",IF(E{last}="",0,E{last}/E{t}))'); body(rs); rs.number_format = "0%"
notes = [
    "The paper supplies no unit times, deliberately: none were recorded, and filling them from memory would break its own rule (§8-1).",
    "Expect the cost in lumps, late: in the source project the largest single cost was a rewrite triggered by a rule that fired on finished chapters (§8-4). Budget for rework, not for lookups.",
    "For reference, what the record does support (§8-2): about 36 hours of verification and integration over two days; 19 working threads, 4 of them extraction-only; 25 corrections; 10 rules derived.",
]
for k, n in enumerate(notes):
    c = cc.cell(row=t + 3 + k, column=1, value=n); c.font = Font(name=F, size=10, italic=True)
    cc.merge_cells(start_row=t + 3 + k, start_column=1, end_row=t + 3 + k, end_column=5)
    c.alignment = WRAP; cc.row_dimensions[t + 3 + k].height = 30

# Example log
ex = wb.create_sheet("Example log v1.1")
title(ex, "Worked example — the source project's log (Appendix A-2, v1.1, lightly condensed)",
      "Error, correction and manner of discovery: grade A (contemporaneous). Component and rule: grade D (applied afterwards by the author). English is the author's translation; the Japanese original governs (published as Appendix A-2 of the Japanese edition from v1.2).")
header(ex, 4, ["#", "Error → Correction", "How it came to notice (A)", "Component (D)", "Rule derived (D)", "Note"], [5, 80, 28, 20, 34, 26])
for i, row in enumerate(EXAMPLE, start=5):
    for j, v in enumerate(row, start=1):
        body(ex.cell(row=i, column=j, value=v))
s = 5 + len(EXAMPLE) + 1
ex.cell(row=s, column=1, value="Provenance entries: 22 of 25 on the author's classification; 19 of 25 if all four contested entries (#7, #16, #17, #20) are moved outside. Redo the count yourself.")
ex.cell(row=s, column=1).font = Font(name=F, size=10, italic=True)
ex.merge_cells(start_row=s, start_column=1, end_row=s, end_column=6)
ex.cell(row=s + 1, column=1, value="Not in this log: effort (no durations), confirmations (kept elsewhere), and five post-publication defects (the log closed at release).")
ex.cell(row=s + 1, column=1).font = Font(name=F, size=10, italic=True)
ex.merge_cells(start_row=s + 1, start_column=1, end_row=s + 1, end_column=6)
ex.freeze_panes = "C5"


# Register of provisions in motion (added in kit v1.1)
REG_COLS = [
    ("Provision\n規定", 30), ("Component\n成分", 14), ("Value as resolved\n確認した値", 36), ("Grade\n評価", 14),
    ("Issuer's source (URL)\n発行者の出典", 34), ("Last resolved\n最終確認日", 13), ("Next check\n次回確認", 16),
    ("Known pending changes (invalidation events)\n値を動かしうる既知の変化", 40), ("Notes\n備考", 30),
]
REG_EXAMPLE = [
    ("India — DPDP Rules 2025, Rules 3, 5–16, 22, 23", "commencement",
     "Eighteen months from publication (month: May 2027 — author's arithmetic)", "period: A | still operative: —",
     "Gazette notification G.S.R. 846(E), 13 Nov 2025, Rule 1(4)", "2026-10-10", "Monthly; and on any MeitY notification",
     "MeitY sought views (Jan 2026) on cutting 18 months to 12; no amending notification found on 2026-10-10",
     "A government explainer (17 Nov 2025) gives the notification date as 14 Nov 2025"),
    ("India — DPDP Rules 2025, Rule 4 (consent managers)", "commencement",
     "Twelve months from publication (month: November 2026)", "A",
     "G.S.R. 846(E), Rule 1(3)", "2026-10-10", "November 2026", "—", ""),
    ("Japan — Corporate Governance Code (July 2026), English edition", "edition",
     "Provisional translation available, dated 21 Jul 2026; posting date not shown", "exists: A | existed on 24 Jul: —",
     "https://www.jpx.co.jp/english/equities/listing/cg/", "2026-10-10", "On any change to the page",
     "—", "Terms differ from the author's translation: General Principle, Interpretive Guidance, reasonableness"),
    ("Japan — NTA Q&A on electronic books (books and documents)", "edition",
     "July 2026 edition listed; posting date not shown", "exists: A | current on 24 Jul: —",
     "https://www.nta.go.jp/law/joho-zeikaishaku/sonota/jirei/4-3.htm", "2026-10-10", "Each June–July",
     "—", "Conflict: a practitioner report (C) says published 10 Jul 2026. Question numbers and pages to be retaken"),
    ("Japan — Electronic Books Regulation art. 5(5)", "identifier",
     "Becomes art. 5(4) on 1 Jan 2027", "A (as recorded in the Q&A)", "NTA Q&A, definitions", "2026-10-10", "2027-01",
     "—", ""),
]

rg = wb.create_sheet("Register in motion")
title(rg, "Register of provisions in motion",
      "Every status component (commencement, edition, existence, dependency) gets a row, an issuer's source and a next-check date. Record what could move the value, not only the value.")
header(rg, 4, [c for c, _ in REG_COLS], [w for _, w in REG_COLS])
for i, row in enumerate(REG_EXAMPLE, start=5):
    for j, v in enumerate(row, start=1):
        body(rg.cell(row=i, column=j, value=v), fill=EX_FILL, color="52606D")
rg.cell(row=5, column=1).comment = Comment("Grey rows: the domain paper's register, re-resolved on 10 Oct 2026. Overwrite or delete them.", "kit")
for rr in range(5 + len(REG_EXAMPLE), 5 + len(REG_EXAMPLE) + 60):
    for j in range(1, len(REG_COLS) + 1):
        body(rg.cell(row=rr, column=j), fill=INPUT_FILL)
dvc = DataValidation(type="list", formula1="=Components!$A$5:$A$20", allow_blank=True)
dvc.showErrorMessage = False
rg.add_data_validation(dvc); dvc.add("B5:B200")
rg.freeze_panes = "B5"

wb.save(os.path.join(OUT, "citation-provenance-kit.xlsx"))

# ---------------------------------------------------------------- CSVs
with open(os.path.join(OUT, "catch_log_template.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow([c.replace("\n", " / ") for c, _ in CATCH_COLS])
    w.writerow(CATCH_EXAMPLE)
with open(os.path.join(OUT, "components.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["component", "ja", "definition", "can_become_false_without_document_changing", "example"])
    w.writerows(COMPONENTS)
with open(os.path.join(OUT, "example_log_v1.1.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["no", "error_to_correction", "how_noticed_gradeA", "component_gradeD", "rule_derived_gradeD", "note"])
    w.writerows(EXAMPLE)
with open(os.path.join(OUT, "register_in_motion_template.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow([c.replace("\n", " / ") for c, _ in REG_COLS])
    w.writerows(REG_EXAMPLE)
print("built")
