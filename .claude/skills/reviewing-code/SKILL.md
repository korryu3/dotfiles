---
name: reviewing-code
description: PRのコードレビューを実施する。固定スキル・専門analyzer・動的観点による多角的レビュー、検証、トリアージ、PRインラインコメント投稿までを一貫して行う。
allowed-tools: Agent, Read, Grep, Glob, Bash(git diff:*), Bash(git log:*), Bash(gh pr diff:*), Bash(gh pr view:*), Bash(gh api:*), Write, AskUserQuestion
---

# Code Review

現在のブランチのPRに対して、複数の観点からコードレビューを実施し、統合レポートを作成する。

## 前提

- PROJECT_ID: `~/.claude/scripts/project-id.sh`を実行して取得する
- 出力先: `~/.claude/context/<PROJECT_ID>/reviews/<branch-name>/`
  - 同名ディレクトリが既に存在する場合は`<branch-name>-1`、`<branch-name>-2`...とサフィックスを付ける

## Phase 1: コンテキスト収集

1. `gh pr view`でPR descriptionと関連issueを取得
2. 変更ファイルの一覧と変更行数を把握（`gh pr diff --stat`）

## Phase 2: スキップ判断

変更内容に応じてPhase 3〜6の各スキル/analyzerのskipを判断する。ドキュメントのみなら全skip、設定ファイルのみなら`/simplify`をskip、diffが極めて小さい（10行以下）ならスキル不要で直接レビューなど。Phase 5のanalyzerも同様（例: テストファイルの変更がなければpr-test-analyzerをskip）。判断に迷う場合はすべて実行する。

## Phase 3: 気になる点の洗い出し

[agents/nitpicker.md](agents/nitpicker.md)のプロンプトでサブエージェントを1体起動する。

出力: `nitpicker.md`

## Phase 4: スキルによるレビュー実行（シーケンシャル）

各スキルは内部でサブエージェントを起動するため、並列実行はできない。

1. `/code-review:code-review` — コード品質・設計・保守性
2. `/simplify` — 冗長性・リファクタリング機会
3. `/security-review` — セキュリティ脆弱性

PRがdraft状態でも、CIが未完了でも実行して構わない。

各スキルの結果を記録: `code-review.md`, `simplify.md`, `security-review.md`（skipしたスキルは作成不要）

## Phase 5: 専門観点によるレビュー実行（並列）

pr-review-toolkitの各analyzerをサブエージェントとして**並列起動**する。

1. `pr-review-toolkit:comment-analyzer` — コメント/ドキュメントの正確性・保守性
2. `pr-review-toolkit:pr-test-analyzer` — テストカバレッジの品質・完全性
3. `pr-review-toolkit:silent-failure-hunter` — サイレントフェイル・不適切なエラーハンドリング
4. `pr-review-toolkit:type-design-analyzer` — 型設計・不変条件・カプセル化

Phase 2のスキップ判断で不要と判定されたanalyzerはスキップする。

各analyzerの結果を記録: `comment-analyzer.md`, `pr-test-analyzer.md`, `silent-failure-hunter.md`, `type-design-analyzer.md`（skipしたanalyzerは作成不要）

## Phase 6: 動的観点レビュー

PRの変更内容から重要なレビュー観点を動的に生成し、各観点ごとにsubagentを並列起動する。

### Step 1: 観点の推論

[agents/perspective-generator.md](agents/perspective-generator.md)のプロンプトでサブエージェントを1体起動する。

### Step 2: レビュー実行

Step 1で生成された各観点に対してサブエージェントを**並列起動**する。各サブエージェントには観点名とレビュー指示をプロンプトとして渡す。

観点が0個の場合はこのPhaseをスキップする。

各観点の結果を記録: `dynamic-{観点名}.md`

## Phase 7: 結果の統合

Phase 3〜6の全結果を統合し、重複を排除した上で**1つのレポート**にまとめる。

- 各指摘に出所ラベルを付与する（`nitpicker` / `code-review` / `simplify` / `security-review` / `comment-analyzer` / `pr-test-analyzer` / `silent-failure-hunter` / `type-design-analyzer` / Phase 6の動的観点名）
- 各指摘にファイルパスと行番号を必ず含める
- 重複する指摘は1つにまとめ、関連する出所ラベルを併記する

出力: `report.md`に書き込む。

### report.mdのフォーマット

```markdown
# Code Review: <branch-name>

## 指摘一覧

- [`nitpicker`] `auth/login.ts:42` — JWTの有効期限がハードコードされている
- [`code-review`] `api/users.ts:15-20` — ページネーション未実装
- [`nitpicker`, `security-review`] `models/order.ts:88` — 既存クエリがソフトデリートを考慮していない
```

## Phase 8: 検証

Phase 7の各指摘に対してSonnetサブエージェント（`model: "sonnet"`を指定）を**並列起動**し、偽陽性を除外する。

各サブエージェントには指摘内容（出所ラベル、ファイルパス、行番号、指摘文）を渡す。

各サブエージェントが行うこと:
1. 該当コードを実際に読み、指摘が正しいか確認する
2. **判定**: 正当な指摘（なぜ問題なのか具体的に記述） / 偽陽性（なぜ問題でないか記述）

偽陽性を除外し、生き残った指摘に検証済みの理由を付与して`report.md`を更新する。

## Phase 9: トリアージ

Phase 8で検証済みの指摘を、PRの目的・変更の文脈を踏まえて分類する。

- 各指摘にアクションレベルを付与する:
  - **must-fix**: マージ前に対応必須（バグ、セキュリティ、データ損失）
  - **should-fix**: 今対応すべきだが、理由があれば見送れる（設計改善、一貫性）
  - **nit**: 対応任意（スタイル、好み、些細な改善）
- must-fix → should-fix → nitの順に並べてユーザーに報告する

## Phase 10: PRへのインラインコメント投稿

Phase 9のトリアージ結果に基づき、**must-fix**と**should-fix**の指摘をPRにインラインコメントとして投稿する。
nitsは投稿せず、ローカルのreport.mdのみに残す。

### 投稿方法

`gh api repos/{owner}/{repo}/pulls/{number}/reviews`でインラインコメント付きレビューを投稿する。

- must-fixが1件以上ある場合: `event=REQUEST_CHANGES`
- must-fixがなくshould-fixのみの場合: `event=COMMENT`
- must-fix/should-fixがいずれもない場合: 投稿しない

### コメントのフォーマット

各インラインコメント:
```
🔴 **[must-fix]** [`code-review`] JWTの有効期限がハードコードされている

**理由**: セキュリティリスク。有効期限の変更にコード修正とデプロイが必要になる

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

```
🟡 **[should-fix]** [`nitpicker`] ページネーション未実装

**理由**: データ量増加時にレスポンスが肥大化し、パフォーマンス劣化を招く

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

レビュー本文（body）:
```
Code Review: N件の指摘（must-fix: X件, should-fix: Y件）

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### 注意事項

- `position`はdiffのハンク内の行位置（ファイルの絶対行番号ではない）
- 他人のPRへの投稿は`guard-pr-posting.sh` PreToolUse hookによりブロックされている
