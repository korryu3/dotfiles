---
name: reviewing-code
description: PRのコードレビューを実施する。コード品質・セキュリティ・複雑性の観点で全指摘を洗い出し、出所ラベル付きでオーケストレーターに返す。トリアージはオーケストレーターが行う。PRレビュー、コードレビュー、pull requestのレビュー依頼時に使用する。
allowed-tools: Agent, Read, Grep, Glob, Bash(git diff:*), Bash(git log:*), Bash(gh pr diff:*), Bash(gh pr view:*), Bash(gh api:*), Write, AskUserQuestion
---

# Code Review

現在のブランチのPRに対して、複数の観点からコードレビューを実施し、統合レポートを作成する。

## 前提

- PROJECT_ID: `~/.claude/scripts/project-id.sh`を実行して取得する
- 出力先: `~/.claude/context/<PROJECT_ID>/reviews/<branch-name>/`
  - 同名ディレクトリが既に存在する場合は`<branch-name>-1`、`<branch-name>-2`...とサフィックスを付ける

## Phase 1: コンテキスト収集

1. `gh pr diff`でPRの差分を取得
2. `gh pr view`でPR descriptionと関連issueを取得
3. 変更ファイルの一覧と変更行数を把握

## Phase 2: スキップ判断

変更内容に応じて不要なスキルをskipする。ドキュメントのみなら全skip、設定ファイルのみなら`/simplify`をskip、diffが極めて小さい（10行以下）ならスキル不要で直接レビューなど。判断に迷う場合はすべて実行する。

## Phase 3: 気になる点の洗い出し

[agents/nitpicker.md](agents/nitpicker.md)のプロンプトでサブエージェントを1体起動する。
Phase 1で収集したdiff全文とPR descriptionをプロンプトに含めること。

出力: `nitpicker.md`

## Phase 4: スキルによるレビュー実行（シーケンシャル）

各スキルは内部でサブエージェントを起動するため、並列実行はできない。

1. `/code-review:code-review` — コード品質・設計・保守性
2. `/simplify` — 冗長性・リファクタリング機会
3. `/security-review` — セキュリティ脆弱性

PRがdraft状態でも、CIが未完了でも実行して構わない。

各スキルの結果を記録: `code-review.md`, `simplify.md`, `security-review.md`（skipしたスキルは作成不要）

## Phase 5: 結果の統合

Phase 3〜4の全結果を統合し、重複を排除した上で**1つのレポート**にまとめる。

- 各指摘に出所ラベル（`nitpicker` / `code-review` / `simplify` / `security-review`）を付与する
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

## Phase 6: 検証

Phase 5の各指摘に対してSonnetサブエージェントを**並列起動**し、偽陽性を除外する。

各サブエージェントには指摘内容（出所ラベル、ファイルパス、行番号、指摘文）を渡す。

各サブエージェントが行うこと:
1. **検証**: 該当コードを実際に読み、指摘が正しいか確認する
2. **理由の明確化**: なぜ問題なのかを具体的に記述する
3. **判定**: 正当な指摘 / 偽陽性（理由付き）

偽陽性と判定された指摘は除外する。生き残った指摘に検証済みの理由を付与して`report.md`を更新する。

## Phase 7: トリアージ

Phase 6で検証済みの指摘を、PRの目的・変更の文脈を踏まえて分類する。

- 各指摘にアクションレベルを付与する:
  - **must-fix**: マージ前に対応必須（バグ、セキュリティ、データ損失）
  - **should-fix**: 今対応すべきだが、理由があれば見送れる（設計改善、一貫性）
  - **nit**: 対応任意（スタイル、好み、些細な改善）
- must-fix → should-fix → nitの順に並べてユーザーに報告する

## Phase 8: PRへのインラインコメント投稿

Phase 7のトリアージ結果に基づき、**must-fix**と**should-fix**の指摘をPRにインラインコメントとして投稿する。
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

レビュー本文（body）:
```
Code Review: N件の指摘（must-fix: X件, should-fix: Y件）

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### 注意事項

- `position`はdiffのハンク内の行位置を指定する（ファイルの絶対行番号ではない）
- `commit_id`はPRのHEAD commitのフルSHAを指定する
- 他人のPRへの投稿は`guard-pr-comment.sh` PreToolUse hookにより構造的にブロックされている
