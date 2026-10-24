# 引用来歴キット（Citation provenance kit）

Ayako Iuchi『What Breaks in a Citation』（v1.1、2026年7月26日）の再現キットです。論文のv1.2（2026年10月12日）から作ったファイルは、そう名乗っています。
キット v1.13（2026年10月24日） · **CC0 1.0**（権利放棄）。許可も表示も不要で、複製・改変・利用できます（例外：引用した政府文書・法令・判決の文言と、法律事務所のニュースレターの数行。「ライセンス」を参照）。

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
| [`examples/es2021_ch6/`](examples/es2021_ch6/) | Blog #21が手作業で監査した章を、パイプラインに通した例。章の文言はインド政府のもので、CC0の対象**外**（キットv1.4） |
| [`tools/notation.py`](tools/notation.py)、[`schema/annotation.schema.json`](schema/annotation.schema.json) | 記法を、英語形と日本語形を1つの文法で読み、型付きの記録（成分、格付け、その成分が動くかどうか）にする。形を検査し（N0〜N7）、2つの形の間で書き換える（キットv1.5） |
| [`examples/method_paper_v1.2/`](examples/method_paper_v1.2/) | 論文v1.2の英日両版にあるすべての注記を、型付きの記録にしたもの（キットv1.5）と、公開されたキャッチログを番号・成分・結果・公開前後だけにしたもの（キットv1.7） |
| [`tools/nulleval.py`](tools/nulleval.py)、[`evals/null/`](evals/null/)、[`schema/null_item.schema.json`](schema/null_item.schema.json) | 空の答えが正解になりうるテスト。5問の問題集、埋めた誤りと空けた誤りと3種類の空を分けて数える採点、記録した実行（キットv1.6） |
| [`tools/catchlog.py`](tools/catchlog.py) | 成分ごとに、公開前と公開後に分けて訂正と確認を別に数え、意味のないゼロを示す（キットv1.7）。`--fields` で各欄の埋まり具合を示す（キットv1.8） |
| [`examples/series_log/`](examples/series_log/) | 論文v1.2より後の著者のログ（ログ#45〜#62）を、発見日、判断の欄、所要時間、公開前後だけにしたもの（キットv1.8）。ログ#45〜#78を、発見日、所要時間、公開前後だけにしたもの（キットv1.13） |
| [`kit/extraction_prompt_2026-07-24_ja.md`](kit/extraction_prompt_2026-07-24_ja.md)、[`_en.md`](kit/extraction_prompt_2026-07-24_en.md) | 元のプロジェクトで2026年7月24日に使った逐語抽出の指示文。原文（日本語）と英訳（キットv1.9） |
| [`kit/extraction_prompt_v2_ja.md`](kit/extraction_prompt_v2_ja.md)、[`_en.md`](kit/extraction_prompt_v2_en.md) | 指示文の改訂版。「このPDFにはない」と検索の記録、PDF頁と印字頁、資料の外から来たものの別の欄（キットv1.9） |
| [`tools/extractcheck.py`](tools/extractcheck.py)、[`schema/extraction.schema.json`](schema/extraction.schema.json) | 抽出の報告を記録の形にしたものと、抽出係が書いているのに報告が示していない識別子の検査（キットv1.9） |
| [`examples/extraction_2026-07-24/`](examples/extraction_2026-07-24/) | 2026年7月24日の抽出の報告4本を写したもの。中の逐語はインドの法令と判決で、CC0の対象**外**（キットv1.9） |
| [`tools/derivedcheck.py`](tools/derivedcheck.py)、[`register/derived.jsonl`](register/derived.jsonl)、[`schema/derived.schema.json`](schema/derived.schema.json) | 派生文書（要約、README、引用情報ファイル、写し）の台帳。それぞれが元にした版を記録し、状態ログにある元の文書のいまの版と比べる。キット自身の版の表記どうし、READMEが挙げるタグと実在のタグも比べる（キットv1.10） |
| [`tools/calccheck.py`](tools/calccheck.py)、[`register/computed.jsonl`](register/computed.jsonl)、[`schema/computed.schema.json`](schema/computed.schema.json) | 算出値（比率、期間から数えた月、件数）の台帳。入力、演算、誰が計算したかを記録し、計算し直したうえで、計算し直しても見つからないもの（入力の格付けをそのまま付けた値など）を挙げる（キットv1.11） |
| [`tools/idcheck.py`](tools/idcheck.py)、[`register/identifiers.jsonl`](register/identifiers.jsonl)、[`register/namespaces.json`](register/namespaces.json)、[`schema/identifier.schema.json`](schema/identifier.schema.json)、[`schema/namespaces.schema.json`](schema/namespaces.schema.json) | 識別子の台帳。それぞれが属する名前空間と、キーの残り（日付と改正対象、題、ファイルのハッシュと版）を記録する。参照を解決し、2つのものが共有する番号とファイル名を挙げ、文中の名乗りのない `#N` のうち2つの名前空間を指しうるものと、名乗った名前空間にない番号を見つける（キットv1.12） |
| [`tools/debtcheck.py`](tools/debtcheck.py)、[`register/deferred.jsonl`](register/deferred.jsonl)、[`schema/deferred.schema.json`](schema/deferred.schema.json) | 見つけて後の版に先送りした修正、行った修正、出た版の台帳。文書ごとに、未払いの件数、最も古いものが待った日数、版が出たのに入らなかったものを報告する（キットv1.13） |
| [`tools/elapsed.py`](tools/elapsed.py) | タグを付けた版ごとに、コミットの時刻から経過時間を出す。経過時間であって、労力ではない（キットv1.13） |
| [`tests/`](tests/) | linter、状態ログ、箇所への分割、検索後の検査、記法の読み取り、空の答えの採点、キャッチログの集計、抽出の検査、派生文書の検査、算出値の検査、識別子の検査、先送りした修正の報告、経過時間の報告のテスト（`python3 -m pytest tests`。スキーマのテストは `jsonschema` が必要で、ない場合は飛ばします） |
| [`evidence/`](evidence/) | 論文の英日両版、v1.1とv1.2にかけた結果。派生文書の検査（キットv1.10）、算出値の検査（キットv1.11）、識別子の検査（キットv1.12）をキットの台帳にかけた結果。先送りした修正の報告、連載のログの所要時間、版ごとの経過時間と、その元になったコミットの時刻（キットv1.13） |
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

何か見つけると終了コード1を返すので、CIで使えます。読むのはテキストだけです。読みが正しいか、出典がまだ有効か、言葉の違う2つの文が矛盾しているかは判断できません。論文v1.1にかけると、のちにログ#26〜#44として記録された欠陥17件（確認のログ#34と、規則の改善のログ#35を除く）のうち8件と、もう1件の一部を見つけました。誰も見つけていなかったものも1件ありました。日本語版で、目次の第3章の題が本文の見出しと一致していません。結果はHypothetical Technical Blog #19『規則はメカニズムではない』で報告しています。

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

## 2種類のゼロ（キットv1.7）

```
python3 tools/catchlog.py LOG.csv            # ワークブックのキャッチログをCSVにしたもの、または no, component, outcome, phase の列を持つCSV
python3 tools/catchlog.py examples/method_paper_v1.2/catch_log.csv
```

訂正だけを数えるログでは、確かめて問題がなかった成分も、一度も確かめていない成分も、同じゼロになります。`catchlog.py` は成分ごとに、公開前と公開後に分けて、訂正と確認を別に数え、各欄を `found`（訂正あり）、`clean`（訂正なし、確認あり）、`other-only`（不記載や規則の改善だけ）、`unexamined`（行がひとつもない）と名付けます。2つを足し合わせることはしません。ワークブックの「キャッチログ」シートをCSVで保存したもの（UTF-8、または日本語版Excelのcp932）と、英語・日本語の成分名を読みます。知らない成分名は報告します（`--strict` なら誤りとして止めます）。綴りを誤った成分があると、本来の成分が「unexamined」に見えてしまうからです。ワークブックの「結果」の選択肢には v1.0 から「confirmed (no error found)」があります。確認も訂正と同じログに記録してください。`examples/method_paper_v1.2/catch_log.csv` は、方法論文の公開されたログ（英語版ログ#1〜#42、日本語版のみログ#43〜#44）を、本文を除いて番号・成分・結果・公開前後だけで持ちます。公開前は頁（page）が `clean`、数値（figure）が `unexamined`（§7-3）。公開後、数値には訂正2件と確認1件があります。論文の3件の不記載（§7-5）は入れていません。論文が番号も成分も示していないためです。

## ほかの誰にも書けない欄（キットv1.8）

```
python3 tools/catchlog.py LOG.csv --fields
python3 tools/catchlog.py examples/series_log/after_v1.2.csv --fields
```

`--fields` は、キャッチログの各欄がどれだけ埋まっているかを、公開前と公開後に分けて報告します。埋まっている、未判断（または記録なし）、空、の3つです。「見逃していたら何が起きたか」と「影響の大きさ」に判断のない項目を番号で挙げます。欄を埋めることはしません。ワークブックとCSVの雛形には、影響の大きさの次に「「見逃していたら」を誰が書いたか」の列を足しました（author、author chose from assistant's options、assistant、not yet decided）。論文はこの欄を委任できない項目と呼びます（§9-5）が、補助者が下書きすることはできてしまうからです。`examples/series_log/after_v1.2.csv` は、論文v1.2より後の著者のログ（ログ#45〜#62、論文には未掲載）を、発見日、判断の欄、所要時間、公開前後だけで持ちます。18件のうち判断があるのは3件で、3件とも補助者の候補から選ばれています。

## このPDFにはない（キットv1.9）

```
python3 tools/extractcheck.py REPORT.json [--source PAGES]
python3 tools/extractcheck.py examples/extraction_2026-07-24/*.json
```

方法論文の最大の設計判断は、逐語抽出を別のスレッドで、解釈を禁じる指示の下で行ったことでした（§8-2）。`kit/extraction_prompt_2026-07-24_ja.md` は、その指示文を使ったときのまま写したもので、英訳を付けています。`kit/extraction_prompt_v2_*.md` はその改訂版です。この指示文を使った4本のスレッドでは、逐語、頁、「見つからない」は守られました。資料が尽きた箇所では、資料が示していないことも報告に入りました。PDFにない条項をどの告示が入れたか、法律上の例外、2つ目の資料との比較です。改訂版はそれを禁じません。「このPDFにはない」と検索の記録、PDF頁と印字頁を求め、資料の外から来たものは出所を付けて別の欄に書かせます。

`extractcheck.py` は `schema/extraction.schema.json` の形の報告を読みます。抽出係が自分の言葉（備考、検索の記録、資料の説明、指示から外れたこと）で書いた識別子のうち、報告の逐語（引用、脚注、表紙の逐語、抽出係が資料の文言として引用符で囲んだ箇所。コードの印（``）は数えず、検索の記録では、検索語に "" やコードの印が使われるので「」と“”だけを数えます）が示しておらず、依頼にもなく、資料の外とも宣言されていないものを挙げます（X2）。検索の記録は、抽出係による資料の説明なので、抽出係の言葉として扱います。報告は1本ずつ検査します。見るのは識別子で、それについて何が言われているかは見ません。「G.S.R. 205(E)が挿入した」は、どこかの逐語が205(E)を示していれば通ります。識別子は、官報の番号とOMの文書番号、事件番号、規則（rule）・節（section）・段落・条（article）の番号と日本語の「条」、判例集の引用、年の付いた規則・法律・規程の題、いくつかの書き方の日付です。列挙と範囲は展開し、日本語の文に接していても拾います。ほかに、資料にないと報告して検索の記録がない項目（X3）、見つかったと報告して頁がない項目（X4）、資料のテキストを渡せば、逐語がその頁にないこと（X1。PDFの頁と印字の頁は分けて照合）を挙げます。数は、異なる識別子の数です。記憶と頁の区別はできません。挙げたものは「示されていない」の意味で、「誤り」の意味ではありません。`examples/extraction_2026-07-24/` は2026年7月の4本の報告を写したものです。写し方と、どこがClaudeの読みかは、そのREADMEにあります。

## 派生文書（キットv1.10）

```
python3 tools/derivedcheck.py --log register/derived.jsonl --status register/status_log.jsonl --on 2026-10-22
python3 tools/derivedcheck.py --tree .                          # このツリー自身の版の表記
python3 tools/derivedcheck.py --tree . --ref v1.2 --expect v1.2 # 公開したタグをgitから読む
git ls-remote --tags origin > tags.txt
python3 tools/derivedcheck.py --tree . --tags @tags.txt          # READMEのタグの一覧と実在のタグ
```

要約、README、引用情報ファイルは、別の文書についての事実を写しています。項目の一覧、件数、版、発行の日付です。元の文書が動くと、写しは一語も変わらずに誤りになります。`register/derived.jsonl` は、派生文書ごとに、元にした文書とその版、それを述べる文書中の言葉（逐語。述べていなければ null）、写している事実、文書が自分に付けた日付、ほかの文書が「発行した」と述べた日、最初に見た日を記録します。状態ログと同じく、追記だけです。元の文書のいまの版は状態ログ（成分 `edition`）から取るので、写しは、文書が変わらなくても偽になりうるほかのすべてと同じ記録と比べられます。

派生文書は、元の文書ごとに1つの判定を受けます。`current`、`stale`（別の版から作った）、`made-from-unknown`（どの版から作ったかを台帳が述べていない）、`source-unknown`（状態ログに元の文書の版がない、または版として読めない）、`source-expired`。印は4つです。`not-in-document`（文書自身が何から作ったかを述べていない）、`claimed-before-observed`（誰も見ていないうちに、ほかの文書が発行済みと書いた）、`unobserved`（発行したとされ、誰も見ていない）、`replaced-by-vN`（台帳に同じ文書の後の版がある。この版もまだ公開されていることがある）。これは報告で、関門ではありません。古い版から作った写しは、記録されている限り stale のままなので、current でないものが1つでもあれば終了コードは1です。最初の行はこの連載自身のものです。本体論文の1枚要約v1.0は、元にした版を最後の行に書いていました。本体論文は2日後（7月26日）にv1.1になり、その行は、要約v1.1を発行した10月13日まで79日間直されませんでした。それを見つけた照合は方法論文のログ#32で、10月12日の論文v1.2に載っています。方法論文v1.2は10月12日に要約v1.1を発行済みと記録しましたが、発行は10月13日でした（ログ#49）。キット自身は論文の2つの版から作ったものとして記録し、判定を2つ受けます。

`--tree` は、キットが自分に付けている版の表記（CITATION.cff、README英日、CHANGELOG、ワークブックのStart hereシート（標準ライブラリで読む）、`build_kit.py`）を集め、食い違えば報告します。`--expect` がなければ、どれが正しいかを決めません。公開したタグにかけると、記録済みの2つの故障がその場所で出ます。v1.2では引用情報ファイルが1.1.1（ログ#47）、ワークブックが1.1（ログ#65）。v1.3〜v1.7ではワークブックが1.1（ログ#65）。v1.9ではワークブックが1.8（`evidence/derivedcheck_2026-10-22.txt`）。テストがこのツリーにかけるので、表記が食い違うリリースは自分のテストで落ちます。各所が挙げる論文の版は一覧にするだけで、判定しません。どのファイルがどの版から来たかは台帳が述べます。`--tags` は、READMEが挙げるタグを、与えたタグと比べます。カンマ区切りの一覧か、1行に1つのタグを書いたファイル、または `git ls-remote --tags origin` の出力をそのまま渡せます。

古い文書のどこが誤りかは言いません。それは読みです。記録した文書しか見えません。lnkd.inのような短縮URLは開けないので、最初に見た日は人が記録します。

## 算出値（キットv1.11）

```
python3 tools/calccheck.py --log register/computed.jsonl --status register/status_log.jsonl --on 2026-10-23 --all
```

`--all` を付けると、後の記録に置き換えられた記録（ここではREADMEの18件。17件が置き換える）も検査します。付けなければ、現行の記録だけです。

比率、期間から数えた月、項目の件数、日数。算出値には、それ自身の出典がありません。あるのは入力と演算と、計算した人です。論文は、こうした値を「AでもDでもない」（§4-6）とし、算術の規則はないと書いています（§9-3）。格付けの横に数字だけを書くと、値は入力の格付けを借り、誰が計算したかはどこにも残りません。計算し直して確かめられるのは算術で、数字の出どころではありません。

`register/computed.jsonl` は、算出値ごとに、示した値とその場所、入力（それぞれの出典、格付け、幅（「強」）や別の値（1つの告示に2つの日付）、予定されている変更、依拠する状態ログの行）、演算（閉じた一覧：割り算、月の加算、日数、分数、件数。`eval()` は使いません）、示した桁、誰が計算したか（`source`、`author`、`assistant`、`unknown`）、それについて文書が何と言っているか、値の横に印刷された格付けを記録します。追記だけです。

値ごとに `recomputes`（計算し直すと一致）か `differs`（一致しない）を返し、次の印を付けます。`grade-borrowed`（出典以外が計算した値にAが付き、格付けにも値にも誰の計算かが書かれていない。閉じた語彙の中では `［数値: A｜帰属: D］`／`[figure: A | attribution: D]` と書き、「著者の計算」「author's arithmetic」などの決まった語も明示とみなす。決まった形だけを読むので、「計算していない」のような否定は読めない）、`operator-unknown`、`claims-disagree`（誰が計算したかについて、文書どうし、または文書と記録の言い分が割れている）、`sensitive`（入力の幅や別の値で、示した桁の値が変わる。変わらなければ robust）、`if-pending`（予定されている変更で値が変わる）、入力が依拠する状態ログの行についての `input-expired`／`input-unrecorded`。判定ではなく報告なので、何か印が付けば終了コードは1です。

最初の記録はこの連載自身のもので、どの値も計算し直すと一致します。本体論文の「about 1.6 per cent」は、そもそも算出値ではありませんでした。判決自身が「約一・六パーセント」と書いているので、記録は計算した者を出典とし、方法論文がそれを著者の計算と説明していることを、食い違う言い分として並べます（v1.2以後の著者のログ#76）。本体論文の「May 2027」は期間から出した著者の計算で、Aの横に置かれています（`grade-borrowed`）。状態ログの同じ月は、値の中で誰の計算かを書いているので、印は付きません。同じ日に記録した状態ログのもう1つの月（規則4の「November 2026」）はそう書いておらず、印が付きます。期間が12か月に縮まれば、2つの5月はどちらも2026年11月になります。記録された2つの公布日では、どちらも変わりません。READMEの「18 defects」（ログ#62）は、足し算は正しく、数える規則が誤っていた例で、除外の幅に `sensitive` が付きます。v1.10のREADMEの79日は、記録が持つもう1つの終点で `sensitive` になります（方法論文は要約v1.1の発行を1日早く書いていた。ログ#49）。出力は `evidence/calccheck_2026-10-23.txt` にあります。

出典が値を自分で書いているかは分かりません。1.6%は3か月のあいだ、計算した値として記録されていました。演算が議論に合っているか（総資産を分母にしてよいか）は言いません。それは読みの問題です。記録された値しか見えません。

## 識別子（キットv1.12）

```
python3 tools/idcheck.py --check
python3 tools/idcheck.py --resolve gsr "206(E)" --key date=2021-03-24
python3 tools/idcheck.py --file path/to/echap06_vol1.pdf
python3 tools/idcheck.py --scan post.txt
```

番号は、名前空間の中でしか一意ではありません。論文が法令について置いた対策は三点キーです。「An identifier is written as number, date, and instrument amended. Never number alone.」（§2-4）。同じ故障は別の形でも起きます。キットv1.2のREADMEは、連載の番号の繰り上げの後も記事を「Hypothetical Technical Blog #18」と引き、指していた記事はBlog #19になっていました（ログ#48）。経済白書の第6章は、2つのパスの下で同じ `echap06_vol1.pdf` という名前を持ち、一方は2018-19年版、もう一方は2020-21年版です。そしてこの連載は、記事にも方法論文のログの項目にも名乗りのない `#` を使い、両者の番号の範囲はいま重なっています。

`register/namespaces.json` は名前空間ごとに、番号以外のキーの項目、文中でその名前空間を名乗る語（`Blog #`、`log #`、`ログ#`）、名乗りのない `#N` がそれを指しうるか、どの番号が存在し、どの番号が予定されているかを宣言します。`register/identifiers.jsonl` は識別子をキーとともに記録します。ダッシュはその項目が確定していないことを示します。追記だけです。

`--check` は `number-shared`（1つの名前空間で2つの記録が番号を共有する。区別できる項目を挙げる）、`date-shared`（日付を共有し番号が違う。論文の言う相補的な形）、`name-shared`（2つのファイルが名前を共有し、中身が違う）、`key-incomplete`（キーの項目がないか、ダッシュ）、`bare-overlap`（名乗りのない `#N` が指しうる2つの名前空間と、共有する番号）を報告します。`--resolve` は `unique`、`ambiguous`（候補を区別できる項目を挙げる）、`mismatch`（番号はあるが、与えたキーとは合わない。そのキーを持つ番号も挙げる）、`absent` を返します。`--file` は各ファイルのハッシュを取り、名前と中身の両方で台帳から探します。`--scan` は文中の `#N` を探し、`named`（名前空間を名乗っている。または名乗った範囲や列挙の続き）、`absent`（名乗ったが、その名前空間にその番号がなく、予定もない）、`unqualified`（名乗りがなく、その番号を持つか予定している名前空間が1つ）、`ambiguous`（名乗りがなく、2つ以上が持つか予定している）、`unknown` に分けます。記号の後ろの語は読まないので、「Blog #18 and #19 of the log」の2つ目は記事として読みます。読むのは `#N` の形だけで、「entry 30」は読みません。URLの中の断片は飛ばし、コードの部分は読みます。`--file` は、正しいファイルでも名前をほかのファイルと共有していれば報告します。書き手がどちらを指したかは決めません。文脈で読み手には明らかなこともあります。報告するのは、その記号だけでは分からないことです。検査は報告であって関門ではなく、何かを報告したときは終了ステータスが1になります。

最初の記録はこの連載自身のものです。G.S.R. 205(E)・206(E)（2021年）と206(E)（2015年）（§2-2）、2021年10月29日の2つの通達（一方の件名は確定していない）、ログ#48のためのBlog #18と#19、そして `echap06_vol1.pdf` という名前の2つの章です。2020-21年版のハッシュは `examples/es2021_ch6/lines.json` が記録したものです。2018-19年版はこの環境からハッシュを取れておらず、取れるまでは `key-incomplete` です。v1.12から、このREADMEは `#N` の形で書く番号すべてに名前空間を名乗らせます。成分の一覧と台帳自身の文も同じで、テストがそれを確かめます。同じ日の先に書いた3つの記録は、番号に名前空間を付けていなかったか、3つの出典から取った事実に出典を1つしか書いていませんでした。それらは書いたまま残し、後の記録が置き換えます。出力は `evidence/idcheck_2026-10-23.txt` にあり、キットに入っていない記事Blog #17〜#31の集計も載せています。

読むのは、記録されたものと書かれたものだけです。どの項目を3つ目のキーにするかは書き手が選びます。ハッシュは、中身が同じでもファイルを保存し直すと変わります（メタデータが変わったPDFなど）。公開済みの記事は直しません。

## 先送りした修正と経過時間（キットv1.13）

```
python3 tools/debtcheck.py register/deferred.jsonl --on 2026-10-24 --list
python3 tools/catchlog.py examples/series_log/through_78.csv --fields
python3 tools/elapsed.py --git . --named
```

論文は、この規律のコストを「is not a smooth per-citation tax. It arrives in lumps, late, when a rule fires on work already believed finished」（§8-4）と書き、所要時間の欄を「on day one」に足すよう勧めます（§8-1）。キットはv1.0からその列を持っています。論文v1.2より後の著者のログ、ログ#45〜#78では、34件すべてで「記録なし」です。人が記入しなければならない欄は規則であって、仕組みではありません。

`register/deferred.jsonl` は3種類の行を記録します。見つけて先送りした修正（「次の版で直す」）とそのログの項目、文書、場所、条件、発見日と記録日。行った修正とその版。出た版。追記だけです。`debtcheck.py` は、ある日の時点で文書ごとに、未払いの件数（条件付きは別に数える）、支払った件数、最も古い未払いとその日数、期限を過ぎたもの（先送りを記録した後にその文書の版が出たのに、修正が入らなかったもの）を報告します。ログに発見日がないときは記録日を使い、そう書きます。数えて日付を出すだけで、修正にどれだけかかるかは言いません。最初の記録はログ自身のものです。方法論文の次の版に先送りした16件（うち2件は条件付き）、本体論文の次の改訂に先送りした1件、キットがv1.3に先送りしてそこで直した2件（ログ#46とログ#47）。期限を過ぎたものはありません。どちらの論文も、その後に版が出ていないからです。台帳にあるのは、ログが先送りとして記録したものです。作業メモの中で先送りし、ログに書かなかった修正は入っていません。

`elapsed.py` はコミットの時刻を読み、タグを付けた版ごとに、前のタグからのコミット数、最初のコミットとタグのコミット、その間の時間を出します。`--named` は、件名がその版を名乗るコミットだけを数えます。経過時間であって、労力ではありません。作業と待ち時間を分けず、最初のコミットの前やgitの外の作業を知らず、並行した作業を1回しか数えません。v1.0〜v1.2はどれも1コミットなので、時間はゼロと出ます。v1.3は1週間を超えますが、その大半は中断です。`--dump` はコミットの時刻をTSVで書き出し、リポジトリがなくても報告を再現できるようにします。出力は `evidence/debtcheck_2026-10-24.txt` にあり、元は `evidence/git_times_2026-10-24.tsv` です。

`catchlog.py --fields` は、印の後に括弧の注記が続く値（「記録なし（2026-10-20には判断待ちとして挙がっていた）」など）も、未記録として読むようになりました。ダッシュの後に注記が続く値は、以前からそう読んでいました。

## このキットがしないこと

何も検証しません。あなたの検証作業が生んだものを記録するだけです。格付けが完璧でも、誤読された文書はありえます。

## キットを使った記事

Hypothetical Technical Blog「引用の来歴」（英語版、note）：

- Blog #17 — [What Broke Was the Provenance, Not the Claim](https://note.com/ayako_iuchi/n/nb5dbd0aa502b)
- Blog #18 — [Commencement Is a Cache-Invalidation Problem](https://note.com/ayako_iuchi/n/n6cbb36bb35c1)（動いている規定の登録簿。キットv1.1で追加）
- Blog #19 — [A Rule Is Not a Mechanism](https://note.com/ayako_iuchi/n/n5adfbe0c66f8)（linter、キットv1.2）
- Blog #20 — [Fixed Words, Moving Status](https://note.com/ayako_iuchi/n/ne5747d7bcd77)（状態ログ、キットv1.3）
- Blog #21 — [A Source Has Sources](https://note.com/ayako_iuchi/n/n7a82eee7a8af)
- Blog #22 — [The Chunk Is the Citation](https://note.com/ayako_iuchi/n/n380de7d3e282)（箇所への分割、検索、検索後の依存の検査。キットv1.4）
- Blog #23 — [The Component Is the Type](https://note.com/ayako_iuchi/n/ndacfe00e9263)（型付きの記録としての記法。キットv1.5）
- Blog #24 — [Not Established Is an Answer](https://note.com/ayako_iuchi/n/n7d7ca5a8837b)（空の答えが正解になりうるテスト。キットv1.6）
- Blog #31 — [Recomputing Is Not Citing](https://note.com/ayako_iuchi/n/nf8adb5ccde85)（算出値と、誰が計算したか。キットv1.11。2026年10月23日、v1.11のリリースとタグの後に公開。日本語版は[こちら](https://note.com/ayako_iuchi/n/n37b6cbf7a377)）。
- Blog #32 — [A Number Is Not a Key](https://note.com/ayako_iuchi/n/ncf262340dc74)（識別子、名前空間、識別子の検査。キットv1.12。2026年10月23日、v1.12のリリースとタグの後に公開。日本語版は[こちら](https://note.com/ayako_iuchi/n/n54ebd37a457c)）。Blog #25〜#30は公開済みで、リンクは追って足します。

リリースのタグは、リリースのコミットが `main` に入った後に、著者がGitHubで付けます。それまでタグはありません。このREADMEを最後に変えた日（2026年10月23日）に存在したタグ：（`v1.0`、`v1.1`、`v1.1.1`、`v1.2`、`v1.3`、`v1.4`、`v1.5`、`v1.6`、`v1.7`、`v1.8`、`v1.9`、`v1.10`、`v1.11`）。v1.11のタグはv1.11のリリースのコミット 19ec6f7 を指し、著者が2026年10月23日9時36分（日本時間）に作りました。v1.10のタグはv1.10のリリースのコミット 1b57c34 を指し、著者が2026年10月23日に作りました。v1.9のタグは時刻を持たない軽量タグで、v1.9のリリースと一緒に作られました。GitHubはそのリリースの公開を10月22日13時22分40秒（日本時間）と記録しています。リリースのコミットの約23時間半後です。v1.9を引くHypothetical Technical Blog #27は、その間に公開されています。Blog #19、#20、#22〜#24は説明している版を挙げているので、そのタグを開くと記事が見ていたときのキットを見られます。Blog #17、#18、#21は版を挙げていません。公開された2026年10月13〜14日には、既定のブランチはv1.2でした。Blog #22、#23、#24は2026年10月20日に、それぞれv1.4、v1.5、v1.6のリリースの後に公開されました。

## 出典

- What Breaks in a Citation — キットv1.0から載せているリンク：[English](https://lnkd.in/p/giTfeMUh) · [日本語](https://lnkd.in/p/gFUXFv2w)。v1.2（Hypothetical Technical Blog #28 が引いたもの）：[English](https://lnkd.in/p/gjQ2RAPW) · [日本語](https://lnkd.in/p/gW5xwpFK)。それぞれがどの版を開くかは、ここからは確かめていません。
- What Your Buyer Is Defending Against（元プロジェクト） — [English](https://lnkd.in/p/gHNjBuCd) · [日本語](https://lnkd.in/p/gF-kd9DF)

実例ログは著者による英訳です。原記録は日本語で付けられ、日本語が優先します。論文のv1.2（2026年10月12日）から、日本語版の付録A-2として公開されます。v1.1では参照されていたものの、公開されていませんでした。成分と規則の列は著者が事後に付けた分類です（D評価）。4件に異論の余地があります（論文の付録A-4）。

## ライセンス

キットはCC0 1.0でパブリックドメインに供されています。ただし、他者から引用した次の文言はCC0の対象外で、キットはその再利用について何の許諾も与えません。

- 経済白書2020-21（インド政府の刊行物）の文言。`examples/es2021_ch6/`（キットv1.4）と、それを使うテストと `evals/null/`（キットv1.4〜v1.6）
- `examples/extraction_2026-07-24/` の抽出の報告に含まれる引用（キットv1.9）。インドの法令、一般財務規則、インド最高裁の判決、法律事務所のニュースレターの数行（題、著作権表示、判例の引用1件）で、抽出係が引いたとおりに収めています
- `register/computed.jsonl` と `evidence/calccheck_2026-10-23.txt` が引く、日本の最高裁判所の判決（1994年1月20日）の数語（キットv1.11）

それらの引用を囲む写しはCC0です。論文は別ライセンスです（『What Breaks in a Citation』本文はCC BY 4.0）。

## コミットメッセージ

Claudeと作ったコミットは、末尾に2行を持ちます。`Co-Authored-By: Claude …` と `Claude-Session: https://claude.ai/code/session_…` です。セッションのリンクは、その変更を行った会話への著者自身の記録で、後から振り返るために残しています。開けるのは著者だけで、共有はしていません。ほかの人が開くと、サインインの画面が出るか、何も表示されません。キットの内容の出典ではありません。決めたことは `CHANGELOG.md` と各ファイルにあります。

## 訂正

訂正を歓迎します（Issueでお知らせください）。黙って直さず、`CHANGELOG.md`に日付付きの改訂として公開します。
