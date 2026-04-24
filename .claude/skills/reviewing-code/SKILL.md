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
2. `gh pr view --json author`と`gh api user`を比較し、PRの作成者が実行ユーザーかどうかを判定する（Phase 6の投稿可否に使用）
3. 変更ファイルの一覧と変更行数を把握（`gh pr diff --stat`）
4. CLAUDE.mdファイルのパス収集（ルート + 変更ディレクトリ配下）
5. `.claude/rules/`配下のルールファイル一覧と、変更ファイルに該当するルールの特定

## Phase 2: 分析 & ルーティング

1. **perspective-generator** (`meta/perspective-generator.md`) のプロンプトでサブエージェントを1体起動し、動的レビュー観点を生成
2. 変更内容に基づき固定枠レビュアーのスキップ判断:
   - ドキュメントのみ → 全固定枠skip、動的観点のみ実行
   - diffが極めて小さい（10行以下）→ bug-scanner + 該当する固定枠のみ
   - 判断に迷う場合は実行する
   - 注意: 「テストファイルの変更なし」「型定義の変更なし」等でレビュアーをスキップしてはならない。テスト未追加や型設計の問題は、該当ファイルが変更されていない場合こそ検出すべき

## Phase 3: 一斉並列レビュー

**固定枠 + 動的枠を全て1ターンで一斉並列起動する。**

各サブエージェントにはPR descriptionと担当観点の指示を渡す。

### 固定枠レビュアー（最大14体、Phase 2のスキップ判断で絞られる）

各レビュアーのエージェントプロンプトは `agents/` 配下に配置。

- **nitpicker** (`meta/nitpicker.md`) — 観点を絞らず気になった点をすべて列挙
- **bug-scanner** (`correctness/bug-scanner.md`) — diff内の明らかなバグをシャロースキャン
- **git-history** (`correctness/git-history.md`) — git blame/履歴から歴史的文脈でバグ・退行を発見
- **past-pr** (`correctness/past-pr.md`) — 過去PRのコメントで今回も該当するものをチェック
- **silent-failure** (`correctness/silent-failure.md`) — サイレントフェイル・不適切なエラーハンドリング
- **claude-md** (`compliance/claude-md.md`) — CLAUDE.mdの規約に準拠しているかチェック
- **rules** (`compliance/rules.md`) — .claude/rules/配下のルールに準拠しているかチェック
- **security** (`specialist/security.md`) — セキュリティ脆弱性
- **reuse** (`quality/reuse.md`) — 既存ユーティリティとの重複、再利用機会
- **code-quality** (`quality/code.md`) — 冗長state、コピペ、leaky abstraction、不要コメント等
- **efficiency** (`quality/efficiency.md`) — 無駄な計算、並列化機会、ホットパス肥大等
- **test-coverage** (`specialist/test-coverage.md`) — テストカバレッジの品質・完全性
- **type-design** (`specialist/type-design.md`) — 型設計・不変条件・カプセル化
- **comment** (`specialist/comment.md`) — コメント/ドキュメントの正確性・保守性

### 共通出力形式

各レビュアー（固定枠・動的枠共通）は以下の形式で出力する:

```
- `file:line` — 指摘内容
  理由: なぜこれが問題か（任意。不明な場合は「理由: 要調査」と記載可）
```

理由が書けないことを理由に指摘を省略しないこと。

### 動的枠レビュアー

Phase 2でperspective-generatorが生成した各観点に対し、サブエージェントを1体ずつ起動する。観点が0個の場合はスキップ。

各動的枠レビュアーのサブエージェントプロンプトに、上記の共通出力形式を指示として含める。

各レビュアーの出力は `{レビュアー名}.md` として保存。

## Phase 4: 統合 + 検証 + トリアージ

### Step 1: 統合・重複排除

Phase 3の全結果を統合し、重複を排除する:
- 各指摘に出所ラベルを付与
- 各指摘にファイルパスと行番号を必ず含める
- 重複指摘は1つにまとめ、関連する出所ラベルを併記
- 複数エージェントが同じ箇所を指摘しWhyが異なる場合は、両方のWhyを併記する

### Step 2: SubAgentによる並列検証

**全指摘に対して、SubAgent(model: Sonnet)を1体ずつ一斉並列起動する。**

各SubAgentへの指示:
- 指摘されたファイル・行番号のコードを実際に読み込む
- 問題が本当に存在するかをコードベースの文脈で確認する。diffのみで判断しないこと。
- 以下のスコアルーブリックに従い、0〜100の信頼度スコアを返す

検証エージェントにはWhyフィールドを含む指摘を渡す。Whyは検証エージェントが「何を確認すべきか」を理解するための文脈情報であり、検証精度の向上に寄与する。ただし、提案生成（How）は検証エージェントから分離する（確認バイアス防止）。

**スコアルーブリック（エージェントに渡す）:**
- **-1**: 本物の問題だが、PRで新たに導入されたものではなく既存の問題
- **0**: 全く確信がない。偽陽性である
- **25**: やや確信あり。本物かもしれないが偽陽性の可能性が高く、検証できなかった
- **50**: 中程度の確信あり。本物の問題と確認できたが、ニトピックまたは実際には発生しにくい
- **75**: 高い確信あり。ダブルチェックし、実際の問題である可能性が非常に高く重要
- **100**: 完全な確信あり。問題であることが確定し、頻繁に発生する

**偽陽性の判断基準（エージェントへの参考情報として渡す）:**
- linter / typecheck / CIが捕まえる問題（importエラー、型エラー、フォーマット等）
- コードの文脈から意図的な変更と判断できるもの
- CLAUDE.mdで言及されているが、lint ignore コメント等でsilenceされているもの

**フィルタリング**:
- スコア **-1**（既存の問題）: 除外せず、別カテゴリとしてレポートに記載する
- スコア **0〜49**: 除外する
- スコア **50〜100**: 正規の指摘としてStep 3のトリアージに進む

### Step 3: トリアージ

検証済みの指摘のみに対してアクションレベルを付与:
- **must-fix**: マージ前に対応必須（バグ、セキュリティ、データ損失）
- **should-fix**: 今対応すべきだが理由があれば見送れる（設計改善、一貫性）
- **nit**: 対応任意（スタイル、好み、些細な改善）

must-fix → should-fix → nitの順でユーザーに報告。

nit指摘のWhyは1文に圧縮してreport.mdに記載する。「理由: 要調査」の場合はreport.mdにはそのまま記載し、PRコメントではWhyブロックを省略する。

出力: `report.md`に書き込む。

### report.mdのフォーマット

```markdown
# Code Review: <branch-name>

## 指摘一覧

### 🔴 must-fix | `auth/login.ts:42`
[`bug-scanner`] スコア: 100

JWTの有効期限がハードコードされている

**理由**: セキュリティリスク。有効期限の変更にコード修正とデプロイが必要になる

**提案**:
環境変数から読み込むように変更する
```typescript
const JWT_EXPIRY = process.env.JWT_EXPIRY ?? 3600;
```

### 🟡 should-fix | `api/users.ts:15-20`
[`nitpicker`] スコア: 75

ページネーション未実装

**理由**: データ量増加時にレスポンスが肥大化し、パフォーマンス問題を引き起こす

**提案**:
limit/offsetパラメータを追加する
```typescript
const { limit = 20, offset = 0 } = req.query;
```

- 💬 **[nit]** [`nitpicker`] `models/order.ts:88` — 既存クエリがソフトデリートを考慮していない可能性がある（理由: deleted_atカラムの追加に伴い、既存クエリの条件にWHERE deleted_at IS NULLが必要）

## 既存の問題（対応検討）

PRで新たに導入された問題ではないが、変更箇所の近辺で検出された既存の問題:

- ⚪ [`bug-scanner`] `auth/login.ts:30` — エラーハンドリングが不足している（理由: 例外発生時にログなく握りつぶされる）
- ⚪ [`code-quality`] `api/users.ts:8` — 未使用のimportが残っている（理由: バンドルサイズへの影響）
```

## Phase 5: 提案生成

Phase 4のトリアージでmust-fix/should-fixと判定された指摘に対して、提案生成エージェントを並列起動する。nitの指摘には起動しない。

提案生成を独立フェーズにする理由: 検証（Phase 4 Step 2）と提案生成は認知的に異なるタスクである。検証エージェントに提案生成を兼務させると「提案を作ったので問題の存在を肯定したくなる」確認バイアスが生じるリスクがある。

オーケストレーターがPhase 4のトリアージ結果をメモリ上で保持し、must-fix/should-fixの指摘を抽出して各提案生成エージェントのプロンプトに直接含めて渡す。渡す内容:
- 指摘内容（What）
- 理由（Why）
- ファイルパス・行番号
- トリアージレベル（must-fix / should-fix）

各指摘に対してSubAgent(model: Sonnet)を1体ずつ一斉並列起動する。エージェントプロンプトは `agents/meta/proposal-generator.md` を参照。

全エージェントの完了を待ってからPhase 6に進む。提案生成エージェントが失敗した場合はHowなしでPhase 6に進む（What + Whyのみで投稿）。

生成された提案はreport.mdの該当指摘に追記する。

## Phase 6: PRへのインラインコメント投稿

Phase 1の判定結果に基づき、PRの作成者が実行ユーザーと異なる場合はPhase 6全体をスキップする。スキップ時はレポートに「他人のPRのため投稿をスキップしました」と記載する。

Phase 4のトリアージ結果に基づき、**must-fix**, **should-fix**, **nits**の指摘をPRにインラインコメントとして投稿する。

### 投稿方法

`gh api repos/{owner}/{repo}/pulls/{number}/reviews`でインラインコメント付きレビューを投稿する。
REQUEST_CHANGESは自身のPRでは使えないため、`event=COMMENT`で投稿すべき。
- must-fix/should-fix/nitsがいずれもない場合: 投稿しない

### コメントのフォーマット

must-fix / should-fixの各インラインコメント（出所ラベルなし）:
```
🔴 **[must-fix]** JWTの有効期限がハードコードされている

**理由**: セキュリティリスク。有効期限の変更にコード修正とデプロイが必要になる

**提案**:
環境変数から読み込むように変更する
```suggestion
const JWT_EXPIRY = process.env.JWT_EXPIRY ?? 3600;
```

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

nitのインラインコメント（1文圧縮、出所ラベルなし）:
```
💬 **[nit]** `user_id` → `userId` にするとプロジェクトの命名規則と統一できる

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

「理由: 要調査」の場合（Whyブロック省略）:
```
🔴 **[must-fix]** JWTの有効期限がハードコードされている

**提案**:
環境変数から読み込むように変更する
```suggestion
const JWT_EXPIRY = process.env.JWT_EXPIRY ?? 3600;
```

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

- 出所ラベル（`[bug-scanner]`等）はPRコメントには含めない
- suggestionブロックはGitHubのsuggested changesとして表示され、ワンクリックで適用可能。ただしdiff内の行のみ置換可能なため、使える場合のみ使用する
- 「理由: 要調査」のWhyブロックはPRコメントでは省略する

レビュー本文（body）も更新:
```
Code Review: N件の指摘（must-fix: X件, should-fix: Y件, nit: Z件）

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### 注意事項

- `position`はdiffのハンク内の行位置（ファイルの絶対行番号ではない）
- 他人のPRへの投稿はスキップ判定で除外される
