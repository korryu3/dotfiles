---
name: reviewing-code-v2
description: 【実験版】オーケストレーター中心のコードレビュー。レンズ型SubAgentを廃止し、Opusオーケストレーターが一次レビュー・検証・提案を一貫して行う。reviewing-codeとの品質比較テスト用。
allowed-tools: Agent, Read, Grep, Glob, Bash(git diff:*), Bash(git log:*), Bash(gh pr diff:*), Bash(gh pr view:*), Bash(gh api:*), Write, AskUserQuestion, TaskCreate, TaskUpdate
---

# Code Review v2（実験版: オーケストレーター中心アーキテクチャ）

現在のブランチのPRに対して、オーケストレーターが主たるレビュアーとしてコードレビューを実施する。

**reviewing-codeとの違い:** レンズ型SubAgent（nitpicker, bug-scanner, silent-failure, claude-md, rules, security, code-quality, efficiency, type-design, comment）を廃止し、オーケストレーター自身が全観点を1パスで適用する。探索型SubAgent（git-history, past-pr, reuse, test-coverage）は維持。

## 前提

- PROJECT_ID: `~/.claude/scripts/project-id.sh`を実行して取得する
- 出力先: `~/.claude/context/<PROJECT_ID>/reviews/<branch-name>/`
  - 同名ディレクトリが既に存在する場合は`<branch-name>-1`、`<branch-name>-2`...とサフィックスを付ける
- エージェントプロンプトは `~/.claude/skills/reviewing-code/agents/` 配下を参照する

## 進捗管理

開始時に以下のTaskを一括生成し、各Taskの開始時にin_progress、完了時にcompletedに更新する:

- Phase 1: コンテキスト収集
- Phase 2 Track A: オーケストレーター一次レビュー
- Phase 2 Track B: 探索型SubAgent並列実行
- [Track A] バグ・正確性
- [Track A] サイレントフェイル
- [Track A] セキュリティ
- [Track A] 型設計
- [Track A] コード品質
- [Track A] 効率
- [Track A] コメント正確性
- [Track A] CLAUDE.md準拠
- [Track A] Rules準拠
- [Track A] PR固有の観点
- Phase 3: 統合 + トリアージ + 提案生成
- Phase 4: PRへのインラインコメント投稿

## Phase 1: コンテキスト収集

1. `gh pr view`でPR descriptionと関連issueを取得
2. `gh pr view --json author`と`gh api user`を比較し、PRの作成者が実行ユーザーかどうかを判定する（Phase 4の投稿可否に使用）
3. 変更ファイルの一覧と変更行数を把握（`gh pr diff --stat`）
4. CLAUDE.mdファイルのパス収集（ルート + 変更ディレクトリ配下）
5. `.claude/rules/`配下のルールファイル一覧と、変更ファイルに該当するルールの特定
6. `gh pr diff`でdiff全文を取得
7. 全変更ファイルの変更箇所周辺をReadで読み込む

## Phase 2: 並列実行

以下のTrack A/Bを**同一ターンで並列実行**する。

### Track A: オーケストレーター一次レビュー

Phase 1で読み込んだコードに対して、レビュー観点ごとにTaskを生成し、1観点ずつ集中してレビューする。

**手順:**

1. 以下の全観点をTaskとして一括生成する（TaskCreate）
2. 各Taskを1つずつin_progressに設定し、**その観点だけに集中して**変更箇所を精査する
3. 指摘を記録したらそのTaskをcompletedにし、次の観点に移る

この構造により、複数観点の同時適用による注意の散漫を防ぎ、各観点で専門SubAgentと同等の深さを確保する。

**生成するTask（レビュー観点）:**

1. **バグ・正確性** — diff内の明らかなバグ、ロジックエラー、off-by-one、null参照
2. **サイレントフェイル** — エラー握りつぶし、不適切なfallback、空catchブロック、log & continue
3. **セキュリティ** — injection、認証バイパス、データ露出、ハードコードされた秘密情報。明確な脆弱性パターンで具体的な攻撃パスを示せるもののみ
4. **型設計** — 不変条件の表現・強制、カプセル化、コンパイル時保証。make illegal states unrepresentable
5. **コード品質** — 冗長state、コピペ亜種、leaky abstraction、文字列リテラル多用、不要コメント（WHATコメント）
6. **効率** — 不要な計算、N+1、並列化機会、ホットパス肥大、メモリリーク
7. **コメント正確性** — コードとの乖離、陳腐化したTODO、誤解を招く記述
8. **CLAUDE.md準拠** — コーディング規約違反（Phase 1で収集したCLAUDE.mdと照合）
9. **Rules準拠** — .claude/rules/違反（Phase 1で特定したルールと照合）
10. **PR固有の観点** — 上記に分類されない、この変更のドメイン・アーキテクチャ固有の懸念

各指摘に対して即座に以下を付与する:
- 確信度スコア（0〜100、確信度スコアルーブリック参照）
- Why（なぜ問題か）
- 提案（must-fix/should-fixレベルの場合）

**確信度スコアルーブリック（問題の実在性のみ）:**
- **-1**: 本物の問題だが、PRで新たに導入されたものではなく既存の問題
- **0**: 偽陽性である
- **25**: 本物かもしれないが、検証できなかった
- **50**: 本物の問題と確認できた
- **75**: ダブルチェックし、本物の問題であると確信
- **100**: 問題であることが確定

問題の深刻度（must-fix/should-fix/nit）はPhase 3 Step 3で別途判断するため、ここでは混ぜないこと。

**偽陽性の判断基準:**
- linter / typecheck / CIが捕まえる問題
- コードの文脈から意図的な変更と判断できるもの
- CLAUDE.mdで言及されているが、lint ignoreコメント等でsilenceされているもの

確信度0は出力に含めない。確信度25以上は出力する。

### Track B: 探索型SubAgent（並列）

以下のSubAgentを一斉並列起動する。各エージェントプロンプトは `~/.claude/skills/reviewing-code/agents/` を参照。

- **git-history** (`correctness/git-history.md`) — git blame/履歴から歴史的文脈でバグ・退行を発見
- **past-pr** (`correctness/past-pr.md`) — 過去PRのコメントで今回も該当するものをチェック
- **reuse** (`quality/reuse.md`) — 既存ユーティリティとの重複、再利用機会
- **test-coverage** (`specialist/test-coverage.md`) — テストカバレッジの品質・完全性

各SubAgentにはPR descriptionを渡す。

各SubAgentの出力形式:

```
- `file:line` — 指摘内容
  理由: なぜこれが問題か（任意。不明な場合は「理由: 要調査」と記載可）
```

各SubAgentの出力は `{レビュアー名}.md` として保存。

## Phase 3: 統合 + トリアージ + 提案生成

### Step 1: Track B指摘の検証

Track Bの全指摘をオーケストレーターが検証する。コードは既にPhase 1でコンテキスト内にあるため、各指摘を1件ずつ確認する。

- 確信度スコアルーブリック（Track Aと同じ）に従いスコアリング
- 確信度0は除外
- 確信度25以上はStep 3のトリアージに進む
- 確信度-1は既存の問題として分離

### Step 2: 統合・重複排除

Track AとTrack B（検証済み）の全指摘を統合し、重複を排除する:
- 各指摘に出所ラベルを付与（Track Aの指摘は該当する観点名、Track Bの指摘はエージェント名）
- 各指摘にファイルパスと行番号を必ず含める
- 重複指摘は1つにまとめ、関連する出所ラベルを併記
- 複数の出所が同じ箇所を指摘しWhyが異なる場合は、両方のWhyを併記する

### Step 3: トリアージ

統合済みの指摘に対して、**問題の深刻度**でアクションレベルを付与する。確信度スコアとは独立に、「この問題が実在するとして、どれだけ深刻か」で判断すること:
- **must-fix**: マージ前に対応必須（バグ、セキュリティ、データ損失、サイレント不整合）
- **should-fix**: 今対応すべきだが理由があれば見送れる（設計改善、一貫性、退行リスク）
- **nit**: 対応任意（スタイル、命名、些細な改善）

must-fix → should-fix → nitの順でユーザーに報告。

### Step 4: Track B指摘への提案生成

Track Bのmust-fix/should-fix指摘に対して、オーケストレーターが修正提案を生成する（Track Aの指摘は既にPhase 2で提案生成済み）。

**提案生成の方針:**
- 確信度が高い場合: 具体的なコード例を提示する
- 確信度が低い場合: 「例えば〜する方法があります」のような提案形式にし、断定を避ける
- GitHubのsuggestionブロック（` ```suggestion `）: diff内の行のみ置換可能という制約がある。使える場合のみ使用する
- Whyが「要調査」の場合: コード文脈のみから提案を生成する
- 修正の影響範囲（他のファイルへの波及）がある場合は明記する

nitの指摘にはWhyを1文に圧縮し、提案は生成しない。「理由: 要調査」の場合はそのまま記載する。

### Step 5: ホリスティックサマリー

全レビューを踏まえて、PRの全体的な評価を1-3文で記述する:
- 主要な懸念点の要約
- 設計判断の妥当性（必要な場合）

report.mdの冒頭（指摘一覧の前）に記載する。

### report.mdのフォーマット

```markdown
# Code Review: <branch-name>

## サマリー

[ホリスティックサマリー: PRの全体的な評価を1-3文で記述]

## 指摘一覧

### 🔴 must-fix | `auth/login.ts:42`
[`セキュリティ`] 確信度: 100

JWTの有効期限がハードコードされている

**理由**: セキュリティリスク。有効期限の変更にコード修正とデプロイが必要になる

**提案**:
環境変数から読み込むように変更する
```typescript
const JWT_EXPIRY = process.env.JWT_EXPIRY ?? 3600;
```

### 🟡 should-fix | `api/users.ts:15-20`
[`効率`] 確信度: 75

ページネーション未実装

**理由**: データ量増加時にレスポンスが肥大化し、パフォーマンス問題を引き起こす

**提案**:
limit/offsetパラメータを追加する
```typescript
const { limit = 20, offset = 0 } = req.query;
```

- 💬 **[nit]** [`コード品質`] `models/order.ts:88` — 既存クエリがソフトデリートを考慮していない可能性がある（理由: deleted_atカラムの追加に伴い、既存クエリの条件にWHERE deleted_at IS NULLが必要）

## 既存の問題（対応検討）

PRで新たに導入された問題ではないが、変更箇所の近辺で検出された既存の問題:

- ⚪ [`バグ・正確性`] `auth/login.ts:30` — エラーハンドリングが不足している（理由: 例外発生時にログなく握りつぶされる）
- ⚪ [`コード品質`] `api/users.ts:8` — 未使用のimportが残っている（理由: バンドルサイズへの影響）
```

出力: `report.md`に書き込む。

## Phase 4: PRへのインラインコメント投稿

Phase 1の判定結果に基づき、PRの作成者が実行ユーザーと異なる場合はPhase 4全体をスキップする。スキップ時はレポートに「他人のPRのため投稿をスキップしました」と記載する。

**PRに投稿しない場合（他人のPR、または指摘なし）は、report.mdの指摘一覧をユーザーにそのまま提示する。** ユーザーがレポートファイルを別途開かなくても結果を確認できるようにする。

Phase 3のトリアージ結果に基づき、**must-fix**, **should-fix**, **nits**の指摘をPRにインラインコメントとして投稿する。

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
