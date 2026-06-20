---
name: reviewing-code
description: PRのコードレビューを実施する。最大14+N体のサブエージェントを一斉並列起動し、オーケストレーターが検証・トリアージ・提案生成を一貫して行う。
allowed-tools: Agent, Read, Grep, Glob, Bash(git diff:*), Bash(git log:*), Bash(gh pr diff:*), Bash(gh pr view:*), Bash(gh api:*), Write, AskUserQuestion, TaskCreate, TaskUpdate
---

# Code Review

現在のブランチのPRに対して、複数の観点からコードレビューを実施し、統合レポートを作成する。

## 前提

- PROJECT_ID: `~/.claude/scripts/project-id.sh`を実行して取得する
- 出力先: `~/.claude/context/<PROJECT_ID>/reviews/<branch-name>/`
  - 同名ディレクトリが既に存在する場合は`<branch-name>-1`、`<branch-name>-2`...とサフィックスを付ける

## 進捗管理

開始時にPhaseごとのTaskを一括生成し、各Phaseの開始時にin_progress、完了時にcompletedに更新する:

- Phase 1: コンテキスト収集
- Phase 2: 分析 & ルーティング
- Phase 3: 一斉並列レビュー
- Phase 4: 統合 + 検証 + トリアージ + 提案生成
- Phase 5: PRへのインラインコメント投稿

## Phase 1: コンテキスト収集

1. `gh pr view`でPR descriptionと関連issueを取得
2. 変更ファイルの一覧と変更行数を把握（`gh pr diff --stat`）
3. CLAUDE.mdファイルのパス収集（ルート + 変更ディレクトリ配下）
4. `.claude/rules/`配下のルールファイル一覧と、変更ファイルに該当するルールの特定

## Phase 2: 分析 & ルーティング

1. **perspective-generator** (`meta/perspective-generator.md`) のプロンプトでサブエージェントを1体起動し、動的レビュー観点を生成
2. 変更内容に基づき固定枠レビュアーのスキップ判断:
   - ドキュメントのみ → 全固定枠skip、動的観点のみ実行
   - diffが極めて小さい（10行以下）→ bug-scanner + 該当する固定枠のみ
   - 判断に迷う場合は実行する
   - 注意: 「テストファイルの変更なし」「型定義の変更なし」等でレビュアーをスキップしてはならない。テスト未追加や型設計の問題は、該当ファイルが変更されていない場合こそ検出すべき

## Phase 3: 一斉並列レビュー

**固定枠 + 動的枠を全て1ターンで一斉並列起動する。**

各サブエージェントにはPR descriptionと担当観点の指示に加え、「結果を `{出力先ディレクトリ}/{レビュアー名}.md` にWriteで書き出すこと」を指示する。

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

各レビュアーは以下の形式で出力する:

```
- `file:line` — 指摘内容
  理由: なぜこれが問題か（任意。不明な場合は「理由: 要調査」と記載可）
```

理由が書けないことを理由に指摘を省略しないこと。

### 動的枠レビュアー

Phase 2でperspective-generatorが生成した各観点に対し、サブエージェントを1体ずつ起動する。観点が0個の場合はスキップ。

各動的枠レビュアーのサブエージェントプロンプトに、上記の共通出力形式を指示として含める。

## Phase 4: 統合 + 検証 + トリアージ + 提案生成

### Step 1: 統合・重複排除

Phase 3の全結果を統合し、重複を排除する:
- 各指摘に出所ラベルを付与
- 各指摘にファイルパスと行番号を必ず含める
- 重複指摘は1つにまとめ、関連する出所ラベルを併記
- 複数エージェントが同じ箇所を指摘しWhyが異なる場合は、両方のWhyを併記する

### Step 2: コード読み込み

全指摘の対象ファイル一覧を抽出（重複排除）し、各ファイルの変更箇所周辺をReadで読み込む。

### Step 3: 検証・スコアリング

オーケストレーターが全指摘を通しで検証する。

**検証の方法:**
- 指摘されたファイル・行番号のコードを確認する
- 問題が本当に存在するかをコードベースの文脈で確認する。diffのみで判断しないこと
- 以下の確信度スコアルーブリックに従い、「問題が実在するか」のみを0〜100で判定する。問題の深刻度はStep 5で別途判断するため、ここでは混ぜないこと

**確信度スコアルーブリック（問題の実在性のみ）:**
- **-1**: 本物の問題だが、PRで新たに導入されたものではなく既存の問題
- **0**: 偽陽性である
- **25**: 本物かもしれないが、検証できなかった
- **50**: 本物の問題と確認できた
- **75**: ダブルチェックし、本物の問題であると確信
- **100**: 問題であることが確定

**偽陽性の判断基準:**
- linter / typecheck / CIが捕まえる問題（importエラー、型エラー、フォーマット等）
- コードの文脈から意図的な変更と判断できるもの
- CLAUDE.mdで言及されているが、lint ignore コメント等でsilenceされているもの

**フィルタリング:**
- スコア **-1**（既存の問題）: 除外せず、別カテゴリとしてレポートに記載する
- スコア **0**: 除外する
- スコア **25**: Step 4に進む
- スコア **50〜100**: Step 5のトリアージに進む

**オーケストレーター追加指摘:**

コードを読む過程でSubAgentが見落とした問題を発見した場合、オーケストレーター自身の指摘として追加する。出所ラベルは`orchestrator`とする。追加指摘にも同じ確信度スコアを適用し、スコア50以上のもののみ追加する。

### Step 4: 未検証指摘の深掘り調査

Step 3でスコア25（検証できなかった）と判定された指摘に対して、SubAgent(model: Sonnet)を1体ずつ一斉並列起動する。該当がなければスキップ。

各SubAgentへの指示:
- 指摘内容とファイル・行番号を渡す
- 関連コードを読み込み、問題が実在するか深掘り調査する
- 確信度スコアルーブリック（Step 3と同じ）に従いスコアを返す

スコア50以上の指摘はStep 5のトリアージに合流する。

### Step 5: トリアージ

検証済みの指摘（スコア50以上）に対して、**問題の深刻度**でアクションレベルを付与する。確信度スコアとは独立に、「この問題が実在するとして、どれだけ深刻か」で判断すること:
- **must-fix**: マージ前に対応必須（バグ、セキュリティ、データ損失、サイレント不整合）
- **should-fix**: 今対応すべきだが理由があれば見送れる（設計改善、一貫性、退行リスク）
- **nit**: 対応任意（スタイル、命名、些細な改善）

`~/.claude/context/<PROJECT_ID>/`配下のADR・plan、およびPR descriptionを参照し、意図的な設計判断に該当する指摘は棄却する。棄却した指摘はレポートの「設計判断による棄却」セクションに記載する。

must-fix → should-fix → nitの順でユーザーに報告。

### Step 6: 提案生成

must-fix/should-fixと判定された指摘に対して、オーケストレーターが修正提案を生成する。

**提案生成の方針:**
- 確信度が高い場合: 具体的なコード例を提示する
- 確信度が低い場合: 「例えば〜する方法があります」のような提案形式にし、断定を避ける
- GitHubのsuggestionブロック（` ```suggestion `）: diff内の行のみ置換可能という制約がある。使える場合のみ使用する
- Whyが「要調査」の場合: コード文脈のみから提案を生成する
- 修正の影響範囲（他のファイルへの波及）がある場合は明記する

nitの指摘にはWhyを1文に圧縮し、提案は生成しない。「理由: 要調査」の場合はそのまま記載する。

### Step 7: ホリスティックサマリー

全レビューを踏まえて、PRの全体的な評価を1-3文で記述する:
- 主要な懸念点の要約
- 設計判断の妥当性（必要な場合）

report.mdの冒頭（指摘一覧の前）に記載する。

### report.mdのフォーマット

````markdown
# Code Review: <branch-name>

## サマリー

[ホリスティックサマリー: PRの全体的な評価を1-3文で記述]

## 指摘一覧

### 🔴 must-fix | `auth/login.ts:42`
[`bug-scanner`] 確信度: 100

JWTの有効期限がハードコードされている

**理由**: セキュリティリスク。有効期限の変更にコード修正とデプロイが必要になる

**提案**:
環境変数から読み込むように変更する
```typescript
const JWT_EXPIRY = process.env.JWT_EXPIRY ?? 3600;
```

### 🟡 should-fix | `api/users.ts:15-20`
[`nitpicker`] 確信度: 75

ページネーション未実装

**理由**: データ量増加時にレスポンスが肥大化し、パフォーマンス問題を引き起こす

**提案**:
limit/offsetパラメータを追加する
```typescript
const { limit = 20, offset = 0 } = req.query;
```

- 💬 **[nit]** [`nitpicker`] `models/order.ts:88` — 既存クエリがソフトデリートを考慮していない可能性がある（理由: deleted_atカラムの追加に伴い、既存クエリの条件にWHERE deleted_at IS NULLが必要）

## 設計判断による棄却

ADR・plan・PR descriptionに記載された設計判断に基づき、以下の指摘を棄却した:

- ⚪ [`bug-scanner`] `auth/login.ts:42` — JWTの有効期限がハードコードされている（棄却理由: ADR-0001により環境変数化は意図的に見送り）

## 既存の問題（対応検討）

PRで新たに導入された問題ではないが、変更箇所の近辺で検出された既存の問題:

- ⚪ [`bug-scanner`] `auth/login.ts:30` — エラーハンドリングが不足している（理由: 例外発生時にログなく握りつぶされる）
- ⚪ [`code-quality`] `api/users.ts:8` — 未使用のimportが残っている（理由: バンドルサイズへの影響）
````

出力: `report.md`に書き込む。

## Phase 5: PRへのインラインコメント投稿

明示的な指示がない場合はPhase 5全体(PR投稿)をスキップする。スキップ時はレポートに「他人のPRのため投稿をスキップしました」と記載する。

**PRに投稿しない場合は、report.mdの指摘一覧をユーザーにそのまま提示する。**

Phase 4のトリアージ結果に基づき、**must-fix**, **should-fix**, **nits**の指摘をPRにインラインコメントとして投稿する。

### 投稿方法

`gh api repos/{owner}/{repo}/pulls/{number}/reviews`でインラインコメント付きレビューを投稿する。
REQUEST_CHANGESは自身のPRでは使えないため、`event=COMMENT`で投稿すべき。
- must-fix/should-fix/nitsがいずれもない場合: 投稿しない

### コメントのフォーマット

must-fix / should-fixの各インラインコメント（出所ラベルなし）:
````
🔴 **[must-fix]** JWTの有効期限がハードコードされている

**理由**: セキュリティリスク。有効期限の変更にコード修正とデプロイが必要になる

**提案**:
環境変数から読み込むように変更する
```suggestion
const JWT_EXPIRY = process.env.JWT_EXPIRY ?? 3600;
```

🤖 Generated with [Claude Code](https://claude.com/claude-code)
````

nitのインラインコメント（1文圧縮、出所ラベルなし）:
````
💬 **[nit]** `user_id` → `userId` にするとプロジェクトの命名規則と統一できる

🤖 Generated with [Claude Code](https://claude.com/claude-code)
````

「理由: 要調査」の場合（Whyブロック省略）:
````
🔴 **[must-fix]** JWTの有効期限がハードコードされている

**提案**:
環境変数から読み込むように変更する
```suggestion
const JWT_EXPIRY = process.env.JWT_EXPIRY ?? 3600;
```

🤖 Generated with [Claude Code](https://claude.com/claude-code)
````

- 出所ラベル（`[bug-scanner]`等）はPRコメントには含めない
- suggestionブロックはGitHubのsuggested changesとして表示され、ワンクリックで適用可能。ただしdiff内の行のみ置換可能なため、使える場合のみ使用する
- 「理由: 要調査」のWhyブロックはPRコメントでは省略する

レビュー本文（body）も更新:
````
Code Review: N件の指摘（must-fix: X件, should-fix: Y件, nit: Z件）

🤖 Generated with [Claude Code](https://claude.com/claude-code)
````

### 注意事項

- `position`はdiffのハンク内の行位置（ファイルの絶対行番号ではない）
- 明示的な指示がない場合、PR投稿はskipする
