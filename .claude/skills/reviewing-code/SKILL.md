---
name: reviewing-code
description: PRのコードレビューを実施する。コード品質・セキュリティ・複雑性の観点で分析し、指摘事項を優先順位付きでユーザーに報告する。PRレビュー、コードレビュー、pull requestのレビュー依頼時に使用する。
allowed-tools: Agent, Read, Grep, Glob, Bash(git diff:*), Bash(git log:*), Bash(gh pr diff:*), Bash(gh pr view:*), Write, AskUserQuestion
---

# Code Review

現在のブランチのPRに対して、複数の観点からコードレビューを実施し、統合レポートを作成する。

## 前提

- PROJECT_ID: `~/.claude/scripts/project-id.sh`を実行して取得する
- 出力先: `~/.claude/context/<PROJECT_ID>/reviews/<branch-name>/`

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

Phase 3〜4の全結果を統合し、重複を排除した上で**1つのレポート**としてユーザーに報告する。
GitHubにレビューコメントを投稿してはならない。

- 各指摘にCritical/High/Medium/Lowの優先度を付与し、優先度の高い順に報告する
- PR全体の判断をApprove/Request Changes/Commentのいずれかで示す

出力: `report.md`に書き込み、かつチャットにもサマリーを表示する。
