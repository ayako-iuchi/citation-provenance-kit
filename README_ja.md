# 引用来歴キット（Citation provenance kit）

Ayako Iuchi『What Breaks in a Citation』（v1.1、2026年7月26日）の再現キットです。
キット v1.6（2026年10月20日） · **CC0 1.0**（権利放棄）。許可も表示も不要で、複製・改変・利用できます（キットv1.4からの例外が1つあります。「ライセンス」を参照）。

※英語版READMEを正本とします。

論文の主張は、AI支援の執筆が壊れやすいのは「出典が何と書いているか」より「出典について何が真か」——日付、版、頁、識別子、施行されているか——だということです。このキットは、書きながらその記録を残すための作業道具一式です。

## 内容

| パス | 中身 |
| --- | --- |
| [`kit/citation-provenance-kit.xlsx`](kit/citation-provenance-kit.xlsx) | キャッチログ、成分リスト、格付けと記法、コスト計算表、論文自身の25件のログ（実例）を1冊にまとめたブック |
| [`csv/catch_log_template.csv`](csv/catch_log_template.csv) | キャッチログの列と例1行（どのツールでも使える形式） |
| [`csv/components.csv`](csv/components.csv) | 10成分、それぞれの定義、仕分けの問い |
| [`csv/example_log_v1.1.csv`](csv/example_log_v1.1.csv) | 論文の付録A-2（v1.1、表現を一部圧縮） |
| [`csv/register_in_motion_template.csv`](csv/register_in_motion_template.csv) | 動いている規定の登録簿：状態の成分、発行者の出典、最終確認日、次回確認日、値を動かしうる既知の変化（キットv1.1） |
| [`tools/citelint.py`](tools/citelint.py) | 成分別格付け引用を使う文書のための小さなlinter。未定義のログ番号、「上記6つ」のような数の不一致、残った制作メモ、目次にあって本文に見出しがない項目、語彙の外の記法、本文に印字された書式記号を検出（キットv1.2） |
| [`schema/`](schema/) | **スナップショット**（ある版のある箇所の文言。一度書いたら変えない）と、**状態の主張**（施行・版・存在・依存・識別子についての、日付付きの記述1件）のJSON Schema（キットv1.3） |
| [`register/status_log.jsonl`](register/status_log.jsonl) | 動いている規定の登録簿を、追記だけのログにしたもの。v1.1の5行のあとに、2026年10月12日の発見を、置き換える行と並べて追加（キットv1.3） |
| [`tools/statuslog.py`](tools/statuslog.py) | 「X日の時点で何を記録していたか」と「今日、何を頼れるか」に答える。期限切れの状態には値を返さない（キットv1.3） |
| [`tools/migrate_register.py`](tools/migrate_register.py) | v1.1の登録簿CSVを状態ログの最初の行に変換する。有効期限を推測で作らない（キットv1.3） |
| [`tools/pdflines.py`](tools/pdflines.py)、[`tools/loci.py`](tools/loci.py) | 頁の配置を使って、章を**箇所**（番号付きの段落、節見出し、脚注）に分ける。各箇所に印字頁の範囲と、スナップショットとしての文言を持たせる（キットv1.4） |
| [`tools/retrieve.py`](tools/retrieve.py) | 箇所の文言だけを対象にしたBM25。出すのは候補で、引用ではない（キットv1.4） |
| [`tools/depaudit.py`](tools/depaudit.py) | 検索の後の検査。文言をハッシュと照らし、記録した依存の辺を1段たどり、引かれた文献の状態を状態ログから指定日時点で付ける（キットv1.4） |
| [`schema/locus.schema.json`](schema/locus.schema.json)、[`schema/dependency.schema.json`](schema/dependency.schema.json) | 箇所（スナップショットをそのまま入れ子にする）と、依存の辺（キットv1.4） |
| [`examples/es2021_ch6/`](examples/es2021_ch6/) | #21が手作業で監査した章を、パイプラインに通した例。章の文言はインド政府のもので、CC0の対象**外**（キットv1.4） |
| [`tools/notation.py`](tools/notation.py)、[`schema/annotation.schema.json`](schema/annotation.schema.json) | 記法を、英語形と日本語形を1つの文法で読み、型付きの記録（成分、格付け、その成分が動くかどうか）にする。形を検査し（N0〜N7）、2つの形の間で書き換える（キットv1.5） |
| [`examples/method_paper_v1.2/`](examples/method_paper_v1.2/) | 論文v1.2の英日両版にあるすべての注記を、型付きの記録にしたもの（キットv1.5）と、公開されたキャッチログを番号・成分・結果・公開前後だけにしたもの（キットv1.7） |
| [`tools/nulleval.py`](tools/nulleval.py)、[`evals/null/`](evals/null/)、[`schema/null_item.schema.json`](schema/null_item.schema.json) | 空の答えが正解になりうるテスト。5問の問題集、埋めた誤りと空けた誤りと3種類の空を分けて数える採点、記録した実行（キットv1.6） |
| [`tools/catchlog.py`](tools/catchlog.py) | 成分ごとに、公開前と公開後に分けて訂正と確認を別に数え、意味のないゼロを示す（キットv1.7、未リリース） |
| [`tests/`](tests/) | linter、状態ログ、箇所への分割、検索後の検査、記法の読み取り、空の答えの採点、キャッチログの集計のテスト（`python3 -m pytest tests`。スキーマのテストは `jsonschema` が必要で、ない場合は飛ばします） |
| [`evidence/`](evidence/) | 論文の英日両版、v1.1とv1.2にかけた結果 |
| [`tools/build_kit.py`](tools/build_kit.py) | ブックとCSVを生成するスクリプト（Python 3、`openpyxl`） |
| [`CHANGELOG.md`](CHANGELOG.md) | 日付付きの改訂履歴 |
| [`LICENSE`](LICENSE) | CC0 1.0 Universal |

## 初日の使い方

1. **成分に名前を付け、リストを閉じる。** `Components`シートの10成分から始め、当てはまらないものを削り、自分の分野に必要なものを足し、使うトークンをすべて定義します。
2. **1つの問いで仕分ける：文書が変わらなくても偽になりうるか。** 該当する成分（施行、版、存在、依存。他分野なら撤回や修正再表示）は、記憶ではなく、書く時点で権威ある台帳から再確認します。
3. **成分ごとに、格付けが分かれるときだけ格付けする。** `［語: A｜施行: —］`。ダッシュは「確定しておらず、主張しない」の意味です。
4. **訂正だけでなく、確認と「書かなかったこと」も記録する。** 確認がなければ分母がありません。書かなかったことを記録しないと、規律が最も働いた場所が最も効いていないように見えます。
5. **「見逃していたら何が起きたか」は自分で書き、公開後もログを閉じない。**

## 元のログになかった列

- **既存の規則は発火したか。** 2つの規則が自らを生んだ故障の再発を防げず、ログにはそれが残りませんでした（付録B、§9-1）。
- **所要時間。** 作業量を記録しておらず、再構成もできません（§8-1）。
- **影響の大きさ。** 「議論の一段が崩れる」と「脚注が1つ死ぬ」の区別（§7-1）を、絞り込める項目にしました。
- **公開前／後。** ログが公開時に閉じたため、公開後の欠陥に番号が付きませんでした（§9-7）。

## コスト計算表

作業ごとに「件数 × 単位時間（分）÷ 60」で時間を出します。単位時間は意図的に空欄にしています。ご自身の値を入れてください。出てきた数値は **D評価** であり、使う場所では必ずそう明記してください。

## linter

```
python3 tools/citelint.py paper.md                                        # 著者のMarkdown原稿
python3 tools/citelint.py paper_from_pdf.txt --format rendered --lang ja  # 公開ファイルから取り出したテキスト
```

何か見つけると終了コード1を返すので、CIで使えます。読むのはテキストだけです。読みが正しいか、出典がまだ有効か、言葉の違う2つの文が矛盾しているかは判断できません。論文v1.1にかけると、のちに#26〜#44として記録された欠陥18件（確認の#34を除く）のうち8件と、もう1件の一部を見つけました。誰も見つけていなかったものも1件ありました。日本語版で、目次の第3章の題が本文の見出しと一致していません。結果はHypothetical Technical Blog #19『規則はメカニズムではない』で報告しています。

## 状態ログ（キットv1.3）

v1.1の登録簿は、1行に1つの値と1つの最終確認日を持ちます。値が動くと、前の値を置いておく場所がありません。行を直すと、かつて別のことを信じていたという記録も消えます。状態ログは行を書き換えません。新しい発見は新しい行として加え、どの行を置き換えるかをその行に書きます。

```
python3 tools/statuslog.py register/status_log.jsonl --list
python3 tools/statuslog.py register/status_log.jsonl --subject "Japan — NTA Q&A on electronic books (books and documents)" --component edition --on 2026-10-11 --believed
python3 tools/statuslog.py register/status_log.jsonl --subject "India — DPDP Rules 2025, Rule 4 (consent managers)" --component commencement --on 2026-11-02
python3 tools/statuslog.py --verify-append yesterday.jsonl today.jsonl
```

2つ目は10月11日の時点で記録していた内容を返します。3つ目は次回確認日を過ぎているので、`"status": "expired"` を返し、値は返しません。期限切れの値を古い値で代用しません。状態はスナップショットに入れないので、検索用に索引する文言が、古くなりうる状態を抱えることはありません。

`migrate_register.py` が有効期限を入れるのは、「次回確認」が日付か一定の間隔を示している行だけです。「ページが変わったら」はどちらでもないので、その行の期限は空（null）のままにし、問い合わせでは `no-expiry-stated` と報告します。

しないこと：何を再確認すべきかを決めること、出典同士の食い違いを解くこと、格付けすること。それはあなたの仕事のままです。

## 型付きの記録としての記法（キットv1.5）

```
python3 tools/notation.py paper_from_pdf.txt            # 形を検査する
python3 tools/notation.py paper_from_pdf.txt --records  # 注記1つにつきJSON 1行
python3 tools/notation.py draft_ja.md --markdown --to en  # コードを除き、すべての注記を英語の形で書く
```

格付け、ダッシュ、スロットがないこと、の3つは違う値です。確定した、考えたが確定しない、記録がない。ツールはこの3つを分けたまま持ち、互いに変換しません。読むのは、格付け1つだけの括弧か、コロンの前に既知の成分を挙げた括弧だけで、Markdownのリンクは読みません。検査するのはテキストに見えることだけです。文法（N0）、語彙（N1）、格付け（N2）、ダッシュの文字（N3）、スロットは3つまで（N4）、同じ成分を2度書かない（N5）、格付けがすべて同じなら分けない（N6）、そして通知として、第1スロットが確定していない（N7）。第1スロットが主張の荷重を支えているか、分けた格付けに意味があるか、成分が定義どおりに使われているか、格付けがどの文書に対して付いたかは判断できません。検査のときは、N0〜N6が何かを報告すると終了ステータス1、ファイルを読めなければ2で終わります。分野の拡張成分は `--extend restatement-status` のように宣言します。

各スロットは `csv/components.csv` から `volatile` を受け取ります。記法は日付を持たないので、動く成分（版、存在、施行、依存）の格付けは、確かめた日にだけ成り立ちます。その日は状態ログに置きます。

## 空の答えが正解になりうるテスト（キットv1.6）

```
python3 tools/nulleval.py evals/null/items.jsonl ANSWERS.json [--readings READINGS.json]
python3 tools/nulleval.py evals/null/items.jsonl --baseline fill   # または empty
```

各スロットの正解は、問いと一緒に渡す証拠に対して決めます。値か、3種類の空（`not-established`、`expired`、`no-record`）のどれかです。採点は6つの結果を数え、合計しません。いちばん大事なのは `filled`（正解が空なのに値を答えた）と `blanked`（正解が値なのに空にした）です。断りの形で始まる散文は、読み手が何をしているかを記録するまで `unread` として残します。2026年10月20日の実行は `evals/null/README.md` にあります。

## 2種類のゼロ（キットv1.7、未リリース）

```
python3 tools/catchlog.py LOG.csv            # ワークブックのキャッチログをCSVにしたもの、または no, component, outcome, phase の列を持つCSV
python3 tools/catchlog.py examples/method_paper_v1.2/catch_log.csv
```

訂正だけを数えるログでは、確かめて問題がなかった成分も、一度も確かめていない成分も、同じゼロになります。`catchlog.py` は成分ごとに、公開前と公開後に分けて、訂正と確認を別に数え、各欄を `found`（訂正あり）、`clean`（訂正なし、確認あり）、`other-only`（不記載や規則の改善だけ）、`unexamined`（行がひとつもない）と名付けます。2つを足し合わせることはしません。ワークブックの「キャッチログ」シートをCSVで保存したもの（UTF-8、または日本語版Excelのcp932）と、英語・日本語の成分名を読みます。知らない成分名は報告します（`--strict` なら誤りとして止めます）。綴りを誤った成分があると、本来の成分が「unexamined」に見えてしまうからです。ワークブックの「結果」の選択肢には v1.0 から「confirmed (no error found)」があります。確認も訂正と同じログに記録してください。`examples/method_paper_v1.2/catch_log.csv` は、方法論文の公開されたログ（英語版#1〜#42、日本語版のみ#43〜#44）を、本文を除いて番号・成分・結果・公開前後だけで持ちます。公開前は頁（page）が `clean`、数値（figure）が `unexamined`（§7-3）。公開後、数値には訂正2件と確認1件があります。論文の3件の不記載（§7-5）は入れていません。論文が番号も成分も示していないためです。

## このキットがしないこと

何も検証しません。あなたの検証作業が生んだものを記録するだけです。格付けが完璧でも、誤読された文書はありえます。

## キットを使った記事

Hypothetical Technical Blog「引用の来歴」（英語版、note）：

- #17 — [What Broke Was the Provenance, Not the Claim](https://note.com/ayako_iuchi/n/nb5dbd0aa502b)
- #18 — [Commencement Is a Cache-Invalidation Problem](https://note.com/ayako_iuchi/n/n6cbb36bb35c1)（動いている規定の登録簿。キットv1.1で追加）
- #19 — [A Rule Is Not a Mechanism](https://note.com/ayako_iuchi/n/n5adfbe0c66f8)（linter、キットv1.2）
- #20 — [Fixed Words, Moving Status](https://note.com/ayako_iuchi/n/ne5747d7bcd77)（状態ログ、キットv1.3）
- #21 — [A Source Has Sources](https://note.com/ayako_iuchi/n/n7a82eee7a8af)
- #22 — [The Chunk Is the Citation](https://note.com/ayako_iuchi/n/n380de7d3e282)（箇所への分割、検索、検索後の依存の検査。キットv1.4）
- #23 — [The Component Is the Type](https://note.com/ayako_iuchi/n/ndacfe00e9263)（型付きの記録としての記法。キットv1.5）

リリースごとにタグを付けています（`v1.0`、`v1.1`、`v1.1.1`、`v1.2`、`v1.3`、`v1.4`、`v1.5`、`v1.6`）。#19、#20、#22、#23は説明している版を挙げているので、そのタグを開くと記事が見ていたときのキットを見られます。#17、#18、#21は版を挙げていません。公開された2026年10月13〜14日には、既定のブランチはv1.2でした。#22と#23は2026年10月20日に、それぞれv1.4とv1.5のリリースの後に公開されました。

## 出典

- What Breaks in a Citation — [English](https://lnkd.in/p/giTfeMUh) · [日本語](https://lnkd.in/p/gFUXFv2w)
- What Your Buyer Is Defending Against（元プロジェクト） — [English](https://lnkd.in/p/gHNjBuCd) · [日本語](https://lnkd.in/p/gF-kd9DF)

実例ログは著者による英訳です。原記録は日本語で付けられ、日本語が優先します。論文のv1.2（2026年10月12日）から、日本語版の付録A-2として公開されます。v1.1では参照されていたものの、公開されていませんでした。成分と規則の列は著者が事後に付けた分類です（D評価）。4件に異論の余地があります（論文の付録A-4）。

## ライセンス

キットはCC0 1.0でパブリックドメインに供されています。例外が1つあります。`examples/es2021_ch6/lines.json` と `examples/es2021_ch6/loci.jsonl` に含まれる経済白書2020-21の文言は、インド政府の刊行物の抜粋です（キットv1.4）。CC0の対象外で、キットはその再利用について何の許諾も与えません。論文は別ライセンスです（『What Breaks in a Citation』本文はCC BY 4.0）。

## 訂正

訂正を歓迎します（Issueでお知らせください）。黙って直さず、`CHANGELOG.md`に日付付きの改訂として公開します。
