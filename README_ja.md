# 引用来歴キット（Citation provenance kit）

Ayako Iuchi『What Breaks in a Citation』（v1.1、2026年7月26日）の再現キットです。
キット v1.2 · **CC0 1.0**（権利放棄）。許可も表示も不要で、複製・改変・利用できます。

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
| [`schema/`](schema/) | **スナップショット**（ある版のある箇所の文言。一度書いたら変えない）と、**状態の主張**（施行・版・存在・依存・識別子についての、日付付きの記述1件）のJSON Schema（キットv1.3、未リリース） |
| [`register/status_log.jsonl`](register/status_log.jsonl) | 動いている規定の登録簿を、追記だけのログにしたもの。v1.1の5行のあとに、2026年10月12日の発見を、置き換える行と並べて追加（キットv1.3、未リリース） |
| [`tools/statuslog.py`](tools/statuslog.py) | 「X日の時点で何を記録していたか」と「今日、何を頼れるか」に答える。期限切れの状態には値を返さない（キットv1.3、未リリース） |
| [`tools/migrate_register.py`](tools/migrate_register.py) | v1.1の登録簿CSVを状態ログの最初の行に変換する。有効期限を推測で作らない（キットv1.3、未リリース） |
| [`tests/test_citelint.py`](tests/test_citelint.py) | linterのテスト（`python3 -m pytest tests`） |
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

何か見つけると終了コード1を返すので、CIで使えます。読むのはテキストだけです。読みが正しいか、出典がまだ有効か、言葉の違う2つの文が矛盾しているかは判断できません。論文v1.1にかけると、のちに#26〜#44として記録された欠陥18件（確認の#34を除く）のうち8件と、もう1件の一部を見つけました。誰も見つけていなかったものも1件ありました。日本語版で、目次の第3章の題が本文の見出しと一致していません。結果はHypothetical Technical Blog #18で報告しています。

## 状態ログ（キットv1.3、未リリース）

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

## このキットがしないこと

何も検証しません。あなたの検証作業が生んだものを記録するだけです。格付けが完璧でも、誤読された文書はありえます。

## 出典

- What Breaks in a Citation — [English](https://lnkd.in/p/giTfeMUh) · [日本語](https://lnkd.in/p/gFUXFv2w)
- What Your Buyer Is Defending Against（元プロジェクト） — [English](https://lnkd.in/p/gHNjBuCd) · [日本語](https://lnkd.in/p/gF-kd9DF)

実例ログは著者による英訳です。原記録は日本語で付けられ、日本語が優先します。論文のv1.2（2026年10月12日）から、日本語版の付録A-2として公開されます。v1.1では参照されていたものの、公開されていませんでした。成分と規則の列は著者が事後に付けた分類です（D評価）。4件に異論の余地があります（論文の付録A-4）。

## ライセンス

キットはCC0 1.0でパブリックドメインに供されています。論文は別ライセンスです（『What Breaks in a Citation』本文はCC BY 4.0）。

## 訂正

訂正を歓迎します（Issueでお知らせください）。黙って直さず、`CHANGELOG.md`に日付付きの改訂として公開します。
