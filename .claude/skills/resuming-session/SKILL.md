---
name: resuming-session
description: 前のセッションの引き継ぎドキュメントを読み込み、現在の状態と照合した上で作業を再開する。引数でファイルパスを指定可能。
allowed-tools: Read, Glob, AskUserQuestion, Bash(git status), Bash(git log), Bash(~/.claude/scripts/project-id.sh)
argument-hint: "~/.claude/context/<PROJECT_ID>/handoffs/YYYY-MM-DD/<トピック>.md"
---

# セッション再開

引き継ぎドキュメントを読み込み、現在の状態と突き合わせた上で作業を再開する。

## 手順

### 1. ドキュメントを探す

引数でファイルパスを受け取れる（例: `/resuming-session ~/.claude/context/-Users-foo-bar/handoffs/2026-01-01/auth-refactor.md`）。

- 引数があればそれを読む
- なければ `~/.claude/scripts/project-id.sh` を実行して PROJECT_ID を取得し、`~/.claude/context/<PROJECT_ID>/handoffs/` 配下の日付ディレクトリを確認し、選択UIを表示する：

```
引き継ぎドキュメント一覧

  1. auth-middleware-refactor（2026-01-01 15:30）
  2. api-error-handling（2026-01-01 18:00）
  3. flow-editor-bugfix（2026-01-01 12:15）

番号で選択してください
```

frontmatter の `session_topic` と `created_at` で一覧を構成する。1つしかなければそのまま読む。

### 2. 事前読み込み

ドキュメントに「次のセッションで読むべきファイル」セクションがあれば、列挙されたファイルを読む。

### 3. 状態照合

`git status` / `git log` で現在の実際の状態と突き合わせる。
食い違いがあれば現状を優先し、ユーザーに報告する。

### 4. 状況報告

以下の形式で報告する：

```
╔══════════════════════════════════════════════════╗
║  セッション再開: <session_topic>                    ║
╚══════════════════════════════════════════════════╝

読み込んだファイル: ~/.claude/context/<PROJECT_ID>/handoffs/YYYY-MM-DD/<トピック>.md
保存日時: YYYY-MM-DD HH:MM

## 状態照合
| 項目 | 引き継ぎ時 | 現在 | 一致 |
|---|---|---|---|
| ブランチ | feature/auth | feature/auth | OK |
| 直近コミット | abc1234 | abc1234 | OK |
| 未コミット変更 | なし | 2ファイル | 差分あり |

## 前回のゴール
（ドキュメントから要約）

## 進捗
| タスク | 状態 |
|---|---|
| ... | 完了 / 進行中 / 未着手 |

## 関連ファイル
（主要なファイルと役割の一覧）

## 次のアクション
（未完了の作業から次にやるべきこと）
```

「どこから再開しますか？」と確認し、ユーザーの指示を待ってから作業を開始する。
