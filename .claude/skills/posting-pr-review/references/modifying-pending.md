# 既存pendingレビューの操作

SKILL.mdのStep 0で既存PENDINGが見つかった場合、またはStep 5で投稿済みコメントの修正・削除が必要になった場合の手順。SKILL.mdの禁止操作・横断原則はここでも適用される。

## 事前確認とバックアップ（この分岐に入ったら必ず最初に行う）

1. pendingの中身を取得し、ローカルに保存する:

```bash
gh api repos/{owner}/{repo}/pulls/{n}/reviews/{review_id} > <作業ディレクトリ>/backup-review.json
```

```bash
gh api repos/{owner}/{repo}/pulls/{n}/reviews/{review_id}/comments --paginate > <作業ディレクトリ>/backup-comments.json
```

2. **このセッションで作成していないpendingの場合、ユーザーがGitHub UIで書いた下書きの可能性がある。バックアップ内容を提示し、AskUserQuestionで続行可否を確認してから操作する**

## 追記（行スレッド）

1件ずつmutation→検証を繰り返す。`rid`はpendingレビューのnode ID（REST一覧の`.node_id`、`PRR_`で始まる）:

```bash
gh api graphql -f query='mutation($rid: ID!, $body: String!) { addPullRequestReviewThread(input: {pullRequestReviewId: $rid, path: "<path>", line: <line>, side: RIGHT, body: $body}) { thread { id comments(first: 1) { nodes { id databaseId } } } } }' -f rid=<PRR_...> -F body=@body.md
```

- 複数行スレッドはinputに`startLine`・`startSide`を追加する（GraphQLはキャメルケース）
- 1件追記するごとに、SKILL.md Step 4と同じGETで件数とpath+body先頭を検証する

## 追記（ファイルレベルスレッド）

上のmutationのinputを`path` + `subjectType: FILE` + `body`に変える（`line`・`side`を外す）。

## レビューbodyの追加・更新は不可

追記分岐では、レビューbody（全体コメント）を設定・更新する検証済みの手段が存在しない（空bodyのpendingへのPUTは422で失敗する）。bodyに載せる内容が必要になったら、**操作せず即ユーザーに報告して指示を仰ぐ**。

## コメント本文の編集

REST `PATCH /pulls/comments/{id}`はpendingコメントには404を返すため使えない。GraphQLで編集する。`id`はコメントのnode ID（REST一覧の`.[].node_id`、`PRRC_`で始まる）:

```bash
gh api graphql -f query='mutation($id: ID!, $body: String!) { updatePullRequestReviewComment(input: {pullRequestReviewCommentId: $id, body: $body}) { pullRequestReviewComment { id } } }' -f id=<PRRC_...> -F body=@body.md
```

編集後、コメント一覧GETでpath+body先頭の反映を検証する。

## コメントの単体削除

```bash
gh api graphql -f query='mutation($cid: ID!) { deletePullRequestReviewComment(input: {id: $cid}) { pullRequestReviewComment { id } } }' -f cid=<PRRC_...>
```

削除後、コメント一覧GETで件数を検証する。レビュー内の全コメントを消してもpendingレビュー自体は残る。

## 削除→再作成（最終手段）

pendingレビュー全体を削除して作り直すのは、**ユーザーの明示指示がある場合か、他の全手段が失敗した場合のみ**。実行前に必ず:

1. 冒頭の「事前確認とバックアップ」が完了していること
2. 削除対象と再作成する内容をユーザーに提示し、AskUserQuestionで承認を得ること

```bash
gh api --method DELETE repos/{owner}/{repo}/pulls/{n}/reviews/{review_id}
```

削除後、SKILL.mdのStep 2〜4（新規投稿）をやり直す。本文はバックアップから復元する。
