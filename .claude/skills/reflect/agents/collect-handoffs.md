---
name: collect-handoffs
description: 当日のセッション引き継ぎドキュメントを収集する
tools: Bash(find:*), Read, Write
model: sonnet
---

# collect-handoffs

指定日のセッション引き継ぎドキュメント（handoffs）を収集・要約し、構造化テキストとして出力ファイルに書き出す。

## 入力（オーケストレーターがプロンプトで渡す）

- 対象日: `YYYY-MM-DD`
- 出力先パス（絶対パスで渡される。Writeにはそのまま使い、`~`を使わない）

## 手順

1. 当日分を検索する: `find ~/.claude/context/ -path "*/handoffs/YYYY-MM-DD/*" -name "*.md"`
2. 各ファイルをReadし、frontmatterのトピック相当キー（`session_topic`等）があればタイトルに使う。なければ本文冒頭から要約する
3. 下記フォーマットで出力先にWriteする

## 出力フォーマット

```markdown
## Handoffs

- **<session_topic>**（<プロジェクトID or ディレクトリ名>）
  - 作業内容の要約: <2-3行。事実のみ、内面の推測・評価語を書かない>
  - 未完了タスク: <引き継ぎに明記されたもののみ列挙>
```

- **該当データがない場合も必ず出力する**: `## Handoffs\n該当なし`
- 検索やReadが失敗した場合: `## Handoffs\n収集失敗: <理由1行>`を出力する（空ファイルにしない）

## 完了報告

最終テキストには出力先パスとファイル数のみを返す。
