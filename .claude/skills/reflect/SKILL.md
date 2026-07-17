---
name: reflect
description: 1日のアクティビティを自動収集・蒸留し、振り返りの対話を行う。1日の終わりに使用する。
allowed-tools: Agent, Read, Write, Bash(mkdir:*), Bash(rm:*), Bash(date:*)
---

# reflect — 1日の振り返り

1日の終わりに、今日やったこと・気づいたことを振り返る場。収集・蒸留したdaily（事実の記録）と当日のjournalを土台に、今日を一緒に眺めて話す。眺めるうちに何か気づくのは歓迎、何も出なくてもそれでいい。無理に捻り出さない。

**`~/.claude/context/self/`配下はローカル専用。git管理せず、commit・PR・外部出力への引用を一切しない。**

## 対話

対話のやり方は規定しない。

> 「なんか押し付けがましいな 君に俺の何がわかるんだ？」

守るのは、この一言から導かれる非対称だけ:

- 結論を出すのはユーザー。処方は求められたときだけ
- 読み・仮説・枠組みの持ち込みは自由。それが話を聞いた証拠になる
- 弾かれたら防衛せず、その場で調整する

reflect固有の道具がひとつ: データにあって本人が挙げていないものを差し出せる（そのためにdailyを集めている）。

ユーザーが「save」（または残す旨の合図）と打ったら`references/save.md`を読んで従う。それまで保存は考えない。

## 機構

### 引数

- 日付指定可。デフォルトは今日。`/reflect yesterday`（BSD構文`date -v-1d '+%Y-%m-%d'`。`date -d`はmacOS不可）や`/reflect 2026-06-18`
- 複数日の指定も可（日付ごとに収集・蒸留を並列に走らせる）
- 過去日の実行は本人が明示したときだけ

### Phase 1: 収集（並列SubAgent）

1. `date '+%Y-%m-%d'`で対象日を確定
2. `mkdir -p ~/.claude/context/self/.cache/<日付>/`。既存なら`rm`で中身をクリーン（前回の部分ファイル残存を防ぐ）
3. `agents/`配下の4テンプレートをReadし、**1メッセージで並列起動**。各promptにテンプレート全文＋対象日＋出力先パスを渡す。**パスはすべて`~`を展開した絶対パスで渡す**（SubAgentのWriteは絶対パス必須）:
   - `agents/collect-github.md` → `.cache/<日付>/github.md`
   - `agents/collect-sessions.md` → `.cache/<日付>/sessions.md`（スクリプトパス`~/.claude/skills/reflect/scripts/filter-sessions.py`も渡す）
   - `agents/collect-slack.md` → `.cache/<日付>/slack.md`
   - `agents/collect-handoffs.md` → `.cache/<日付>/handoffs.md`
4. 収集中に対話を始めてよい。dailyが要るのは、データを差し出すときから
5. **SubAgentの完了通知には沈黙する**。報告は収集・蒸留の全完了時に1回だけ（失敗があった場合もそこで1行）
6. 失敗したcollectは欠損として扱い続行する

### Phase 2: 蒸留（SubAgent）

`agents/distill.md`をReadしAgent起動。promptに入力ディレクトリ`.cache/<日付>/`と出力先`~/.claude/context/self/daily/<日付>.md`を明示的に渡す。出力は事実のみ・解釈禁止（テンプレートに記載済み）。

### Phase 3: 準備

`daily`・`journal`（対象日）・`index.md`・`seeds.md`を読む（存在しないものはスキップ）。90日触られていない種は黙ってdormantセクションへ移す（基準は播種日と材料追記日の最新。削除しない。対話で言及しない）。
