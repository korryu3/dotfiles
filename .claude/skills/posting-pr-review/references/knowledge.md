# 根拠とトラブルシューティング

手順の規範はSKILL.mdと`modifying-pending.md`が持つ。このファイルは根拠（エビデンス）と診断ヒントのみを記載する。

## 目次

- [エビデンス表](#エビデンス表)
- [トラブルシューティング](#トラブルシューティング)

## エビデンス表

エビデンスラベル: **doc**=公式ドキュメントで裏取り済み / **実測**=実際のPRで動作確認済み / **未検証**=推定のみ

| # | 知見 | エビデンス |
|---|---|---|
| 1 | `POST /pulls/{n}/reviews`で`event`を省略するとPENDINGになる。`event: "PENDING"`は無効値でエラー | doc（「By leaving this blank, you set the review action state to PENDING」）+実測2回 |
| 2 | 1ユーザーが1つのPRに持てるpendingレビューは1つ。既存があると新規POSTは失敗する | 実測。docに記載なし |
| 3 | pendingコメントはREST `PATCH /pulls/comments/{id}`で編集できない（404） | 実測1回。docは404条件を明記しておらず、仕様でなく観測事実 |
| 4 | GraphQL `updatePullRequestReviewComment`（input: `pullRequestReviewCommentId`, `body`）でpendingコメントを編集できる | 実測1回 |
| 5 | GraphQL `addPullRequestReviewThread`（input: `pullRequestReviewId`にpendingのnode ID）で既存pendingに行スレッドを追記できる | 実測1回 |
| 6 | 同mutationの`subjectType: FILE`でファイルレベルスレッド（行に紐づかない指摘）を追記できる | 実測1回 |
| 7 | GraphQL `deletePullRequestReviewComment`（input: `id`）でpendingコメントを単体削除できる | 実測1回 |
| 8 | bodyが空のpendingレビューは`PUT /pulls/{n}/reviews/{id}`でbodyを設定できない（422「Could not edit a review with a missing body」）。bodyが非空の場合にPUTが効くかは**未検証** | 実測1回（空body側のみ） |
| 9 | `comments[]`は`path`+`line`+`side`指定でよい（`position`計算は不要）。複数行は`start_line`/`start_side`、GraphQL側は`startLine`/`startSide` | doc+スキーマ+実測 |
| 10 | `line`はRIGHT側（削除行はLEFT側）のファイル絶対行番号で、diffハンク内にあること | 実測（行ずれ6件を事前検証で修正した実績） |
| 11 | pendingレビューのコメント一覧（`GET /reviews/{id}/comments`）は`line`フィールドがnullで返る。投稿後検証はpath+body先頭で照合する | 実測 |
| 12 | pending削除は`DELETE /pulls/{n}/reviews/{id}`。submit済みレビューは削除不能 | doc |
| 13 | POST一括作成（comments[]）は1件でも無効なら全体失敗（原子的）と推定 | **未検証**（標準的挙動からの推定） |
| 14 | diff外ファイルへの指摘はインライン・ファイルレベルとも不可 → review bodyのみ。ただし#8により空bodyで作った後からは足せない | 実測+#8 |
| 15 | `gh`コマンドを1行に2つ繋げると2つ目が404で失敗する | 実測1回。詳細は下記トラブルシューティング |

## トラブルシューティング

- **2つ目の`gh`が404**: `gh`を1行に2つ連結すると、2つ目が認証エラーではなく404で失敗する（環境のprehookによるtoken埋め込みがワンラインずつのため）。「リソースが消えた」と誤診しやすい症状で、対象リソースは実在していることが多い
- **REST PATCHの404**: pendingコメントへの`PATCH /pulls/comments/{id}`の404は「コメントが存在しない」ではない（#3）。編集はGraphQL `updatePullRequestReviewComment`で行う
- **POSTの422**: アンカー不正（ハンク外の行番号・diff外のpath等）が典型。`validate_anchors.py`の事前検証で防げる
- **PUTの422「Could not edit a review with a missing body」**: 空bodyのpendingにbodyを後付けしようとした症状（#8）。APIでは回復不能なので、bodyが必要ならユーザーに報告して指示を仰ぐ
