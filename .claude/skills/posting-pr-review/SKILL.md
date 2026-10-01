---
name: posting-pr-review
description: GitHub PRへのレビューコメントをpendingレビュー（下書き）としてAPIで投稿する手順。レビュー指摘をPRにインラインコメント投稿するとき、既存pendingレビューの追記・編集・削除が必要なとき、reviewing系skillのPhase 5から投稿するときに使用する。
allowed-tools: Bash(gh api:*), Bash(gh pr diff:*), Bash(gh pr view:*), Bash(python3:*), Read, Write, AskUserQuestion
---

# PRレビューのpending投稿

GitHub PRへのレビューコメント投稿を、常にpendingレビュー（下書き）として安全に行うAPI手順。

## 前提と責務境界

- 成果物は常に**pendingレビュー**。submitは常にユーザーのGitHub UI操作であり、本skillは一切submitしない
- 本skillはAPI手順のみを規定する。コメントの文体・書式は呼び出し元skill（reviewing-code / reviewing-critical）とreview-comment-styleが規定する
- 進捗報告は「posting Step N」と表記する（reviewing系のPhase 4内部のStep 1〜7と区別するため）

## 禁止操作

pendingを壊す操作は呼ばない:

- `event`付きのレビューPOST（`COMMENT` / `APPROVE` / `REQUEST_CHANGES`のいずれも）。eventは省略してPENDINGにする
- submit系エンドポイント: `POST /pulls/{n}/reviews/{id}/events`、GraphQL `submitPullRequestReview`
- `gh pr review`コマンド（即公開のsubmitになる）

pendingレビュー全体の削除→再作成は、**ユーザーの明示指示がある場合か最終手段のみ**。手順は`references/modifying-pending.md`。

## 横断原則

- エラー発生時・結果不明時は即ユーザーに報告する。POSTは非冪等のため、リトライ前に必ずGETで現状を確認する
- 呼び出し形は各Stepに記載の形をそのまま使う（`{owner}`等のプレースホルダと本文のみ置換する）

## チェックリスト

作業開始時に以下をコピーして進捗管理する:

```
- [ ] posting Step 0: 状態確認（既存pendingの有無）
- [ ] posting Step 1: 本文準備
- [ ] posting Step 2: アンカー決定+機械検証
- [ ] posting Step 3: 投稿（POST一括・event省略）
- [ ] posting Step 4: 検証（state・件数・内容）
- [ ] posting Step 5: 修正（必要な場合のみ）
- [ ] posting Step 6: 完了報告（pendingのまま終了）
```

## Step 0: 状態確認

自分のloginを確認し、PRに対する自分の全レビューを取得してPENDINGの有無を確認する:

```bash
gh api user --jq '.login'
```

```bash
gh api repos/{owner}/{repo}/pulls/{n}/reviews --paginate --jq '[.[] | select(.user.login=="<自分のlogin>")] | .[] | {id, node_id, state}'
```

**PENDINGのレビューが存在する場合はここで主経路を離れ、`references/modifying-pending.md`を読んでそれに従う**（1ユーザーが1つのPRに持てるpendingは1つで、既存があると新規POSTは失敗する）。

## Step 1: 本文準備

コメント本文の書式は呼び出し元skillの規定に従う。呼び出し元がない単体起動時:

- 他人のPR宛 → review-comment-styleの文体規範に従う
- 自分のPRへのセルフレビュー → AskUserQuestionで書式をユーザーに確認する

## Step 2: アンカー決定+機械検証

各指摘のアンカーを4択から決める:

| 形 | 指定 |
|---|---|
| 単一行 | `path` + `line` + `side`。変更後の行は`RIGHT`、削除された行は`LEFT`。`line`はファイル絶対行番号でdiffハンク内にあること |
| 複数行 | 単一行の指定に加えて`start_line` + `start_side`（`line`は範囲の末尾行） |
| ファイルレベル | `path`のみ（行に紐づかない指摘。Step 3で行コメントのPOST後に追記する） |
| review body | diff外ファイルへの指摘はインライン・ファイルレベルとも不可のためbodyに載せる |

diffを保存し、スクリプトを**実行**して機械検証する:

```bash
gh pr diff {n} > <作業ディレクトリ>/pr.diff
```

```bash
python3 ~/.claude/skills/posting-pr-review/scripts/validate_anchors.py <作業ディレクトリ>/pr.diff < anchors.json
```

anchors.jsonはJSON配列`[{"path": str, "line": int?, "side": ("RIGHT"|"LEFT")?}]`。invalidが出たらアンカーを修正してから先へ進む（そのままPOSTすると422で失敗する）。

ここで**bodyに載せる内容の有無を確定する**（diff外指摘があるか、ユーザーからbodyの指定があるか）。

## Step 3: 投稿

review.jsonを作成し、一括POSTする。**eventは省略する**（省略するとPENDINGになる。`event: "PENDING"`は無効値）:

```bash
gh api repos/{owner}/{repo}/pulls/{n}/reviews --input review.json
```

review.jsonの形（`body`キーはStep 2で載せる内容があると確定した場合のみ。なければキー自体を書かない）:

```json
{
  "body": "diff外指摘やユーザー指定の全体コメント",
  "comments": [
    {"path": "src/a.ts", "line": 127, "side": "RIGHT", "body": "..."},
    {"path": "src/b.ts", "start_line": 10, "start_side": "RIGHT", "line": 15, "side": "RIGHT", "body": "..."}
  ]
}
```

- **bodyに載せる内容がある場合は必ずこの初回POSTに含める。指定がない場合は付けない**。空bodyで作成すると後からAPIでbodyを設定できないため、初回POSTが唯一のタイミング
- ファイルレベルの指摘がある場合: 上記POSTのレスポンスの`node_id`（`PRR_`で始まる）を使い、1件ずつ追記する:

```bash
gh api graphql -f query='mutation($rid: ID!, $body: String!) { addPullRequestReviewThread(input: {pullRequestReviewId: $rid, path: "<path>", subjectType: FILE, body: $body}) { thread { id } } }' -f rid=<PRR_...> -F body=@body.md
```

## Step 4: 検証

投稿のたびにGETで確認する:

```bash
gh api repos/{owner}/{repo}/pulls/{n}/reviews/{review_id} --jq '{state, body}'
```

```bash
gh api repos/{owner}/{repo}/pulls/{n}/reviews/{review_id}/comments --paginate --jq '.[] | {path, body: .body[0:80]}'
```

- `state`が`PENDING`であること
- コメント件数が投稿した件数と一致すること
- 各コメントを`path`+`body`先頭で照合する（pendingコメント一覧の`line`はnullで返るため、行番号では照合できない）

## Step 5: 修正（必要な場合のみ）

投稿済みpendingコメントの本文修正・削除が必要になった場合は、`references/modifying-pending.md`を読んでそれに従う。

## Step 6: 完了報告

以下を必ず報告して終了する:

- pendingレビューのまま完了したこと（まだ公開されていない）
- submitはユーザーがGitHub UIで行うこと（レビュー全体コメントもsubmit時にユーザーがUIで書ける）

## References

- `references/modifying-pending.md` — 既存pendingレビューの追記・編集・削除、削除→再作成の最終手段手順
- `references/knowledge.md` — 各手順の根拠（エビデンス表）とトラブルシューティング。エラー時や根拠が必要なときに読む
