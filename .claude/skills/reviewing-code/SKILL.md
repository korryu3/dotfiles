---
name: reviewing-code
description: PRのコードレビューを実施する。最大14+N体のサブエージェントを一斉並列起動し、多角的レビュー・統合・トリアージ・PRインラインコメント投稿までを一貫して行う。
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
3. CLAUDE.mdファイルのパス収集（ルート + 変更ディレクトリ配下）
4. `.claude/rules/`配下のルールファイル一覧と、変更ファイルに該当するルールの特定

## Phase 2: 分析 & ルーティング

1. [agents/meta/perspective-generator.md](agents/meta/perspective-generator.md)のプロンプトでサブエージェントを1体起動し、動的レビュー観点を生成
2. 変更内容に基づき固定枠レビュアーのスキップ判断:
   - ドキュメントのみ → 全固定枠skip、動的観点のみ実行
   - diffが極めて小さい（10行以下）→ bug-scanner + 該当する固定枠のみ
   - 判断に迷う場合は実行する
   - 注意: 「テストファイルの変更なし」「型定義の変更なし」等でレビュアーをスキップしてはならない。テスト未追加や型設計の問題は、該当ファイルが変更されていない場合こそ検出すべき

## Phase 3: 一斉並列レビュー

**固定枠 + 動的枠を全て1ターンで一斉並列起動する。**

各サブエージェントにはPR descriptionと担当観点の指示を渡す。

### 固定枠レビュアー（最大14体、Phase 2のスキップ判断で絞られる）

| レビュアー | agentファイル | 観点 |
|---|---|---|
| nitpicker | [agents/meta/nitpicker.md](agents/meta/nitpicker.md) | 観点を絞らず気になった点をすべて列挙 |
| bug-scanner | [agents/correctness/bug-scanner.md](agents/correctness/bug-scanner.md) | diff内の明らかなバグをシャロースキャン |
| git-history | [agents/correctness/git-history.md](agents/correctness/git-history.md) | git blame/履歴から歴史的文脈でバグ・退行を発見 |
| past-pr | [agents/correctness/past-pr.md](agents/correctness/past-pr.md) | 過去PRのコメントで今回も該当するものをチェック |
| silent-failure | [agents/correctness/silent-failure.md](agents/correctness/silent-failure.md) | サイレントフェイル・不適切なエラーハンドリング |
| claude-md | [agents/compliance/claude-md.md](agents/compliance/claude-md.md) | CLAUDE.mdの規約に準拠しているかチェック |
| rules | [agents/compliance/rules.md](agents/compliance/rules.md) | .claude/rules/配下のルールに準拠しているかチェック |
| security | [agents/specialist/security.md](agents/specialist/security.md) | セキュリティ脆弱性 |
| reuse | [agents/quality/reuse.md](agents/quality/reuse.md) | 既存ユーティリティとの重複、再利用機会 |
| code-quality | [agents/quality/code.md](agents/quality/code.md) | 冗長state、コピペ、leaky abstraction、不要コメント等 |
| efficiency | [agents/quality/efficiency.md](agents/quality/efficiency.md) | 無駄な計算、並列化機会、ホットパス肥大等 |
| test-coverage | [agents/specialist/test-coverage.md](agents/specialist/test-coverage.md) | テストカバレッジの品質・完全性 |
| type-design | [agents/specialist/type-design.md](agents/specialist/type-design.md) | 型設計・不変条件・カプセル化 |
| comment | [agents/specialist/comment.md](agents/specialist/comment.md) | コメント/ドキュメントの正確性・保守性 |

### 動的枠レビュアー

Phase 2でperspective-generatorが生成した各観点に対し、サブエージェントを1体ずつ起動する。観点が0個の場合はスキップ。

各レビュアーの出力は `{レビュアー名}.md` として保存。

## Phase 4: 統合 + トリアージ

1. Phase 3の全結果を統合し、重複を排除
   - 各指摘に出所ラベルを付与
   - 各指摘にファイルパスと行番号を必ず含める
   - 重複指摘は1つにまとめ、関連する出所ラベルを併記
   - 明らかな偽陽性を除外する（既存の問題、linter/CIが捕まえるもの、意図的な変更、PRで変更していない行の問題）
2. 各指摘にアクションレベルを付与:
   - **must-fix**: マージ前に対応必須（バグ、セキュリティ、データ損失）
   - **should-fix**: 今対応すべきだが理由があれば見送れる（設計改善、一貫性）
   - **nit**: 対応任意（スタイル、好み、些細な改善）
3. must-fix → should-fix → nitの順でユーザーに報告

出力: `report.md`に書き込む。

### report.mdのフォーマット

```markdown
# Code Review: <branch-name>

## 指摘一覧

- 🔴 **[must-fix]** [`bug-scanner`] `auth/login.ts:42` — JWTの有効期限がハードコードされている
- 🟡 **[should-fix]** [`nitpicker`] `api/users.ts:15-20` — ページネーション未実装
- 🟢 **[nit]** [`nitpicker`, `security`] `models/order.ts:88` — 既存クエリがソフトデリートを考慮していない
```

## Phase 5: PRへのインラインコメント投稿

Phase 4のトリアージ結果に基づき、**must-fix**と**should-fix**の指摘をPRにインラインコメントとして投稿する。
nitsは投稿せず、ローカルのreport.mdのみに残す。

### 投稿方法

`gh api repos/{owner}/{repo}/pulls/{number}/reviews`でインラインコメント付きレビューを投稿する。

- must-fixが1件以上ある場合: `event=REQUEST_CHANGES`
- must-fixがなくshould-fixのみの場合: `event=COMMENT`
- must-fix/should-fixがいずれもない場合: 投稿しない

### コメントのフォーマット

各インラインコメント:
```
🔴 **[must-fix]** [`bug-scanner`] JWTの有効期限がハードコードされている

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
