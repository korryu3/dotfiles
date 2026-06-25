## 姿勢

- ユーザーは思考停止な同調を極端に嫌う。ユーザーと共に目的を達成せよ。
  - ただし、このルールは「無批判で議論をせずに従うな」であって「何でも代案を出せ」ではない。

## 開発スタイル

- TDDで開発する
  - 開発時は`/tdd`スキルを使うこと。
- バグ調査・デバッグ時は`/diagnose`スキルを使うこと（`superpowers:systematic-debugging`は使わない）
- 不明瞭な指示は質問して明確にする

## コード設計

プログラムを実装する際は以下に準ずること

- 関心の分離を保つ
- 状態とロジックを分離する
- コントラクト層（API/型）を厳密に定義し、実装層は再生成可能に保つ
- 静的検査可能なルールは、プロンプトではなくその環境のlinterかast-grepで記述する

## 外部出力の境界ルール

- 外部から見える成果物（commit message, PR description, コードコメント, PRレビューコメントなど）には、そのコード変更自体から読み取れる事実のみを書く。
  - commit messageのCo-Authored-Byは書くこと
  - commit messageにClaude-Sessionは含めない
- 内部コンテキスト（設定、スキル、メモ、内部番号等）は一切含めない。
- ローカルメモ（`~/.claude/context/`配下）には制約なく自由に書いてよい。

## その他重要なこと

- デザインに関する決定事項を議論する際は、根拠を持って明確な推奨案を提示してください。
  - 必ず対応するコードやドキュメントを読んでから議論すること
- 日本語と英語の間にスペースを入れない（例: ✕「React を使用」→ ○「Reactを使用」）
- memoや残しておきたいことは`~/.claude/context/<PROJECT_ID>/notes/`配下に保存する。PROJECT_IDは`~/.claude/scripts/project-id.sh`で取得する。
- 設計判断の意思決定をした際は、記録を残すためにADRを作成する。
  - 特別な指示がない限り、`~/.claude/context/<PROJECT_ID>/adr/`配下に保存する。
- アーキテクチャやワークフローをPR descriptionなどに記載する際はmermaidで書くこと
- commit messageはConventional Commitsに従い、日本語で書く
- SubAgentには不可逆操作 (push/外部送信等) は委譲せず、必ずオーケストレーター自身が実装を確認した後に操作をする
  - commitはok
- 使ってない/役割の終えたチームメイトはshutdown_requestでkillする
- PR作成ルール：draft, ユーザーをアサインする
- ユーザーの指示や許可がない限りサーバー起動は自力でやらない。
- superpowers系のskillの出力はcommitしない(gitignore済み)
- ghコマンドは一行ずつbash実行すること
  - prehookのgh token埋め込みがワンラインずつしか効かないため。
  - 最初や途中にechoを書くとghが失敗する可能性があります。
