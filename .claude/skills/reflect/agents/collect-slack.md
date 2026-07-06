---
name: collect-slack
description: 当日の自分のSlack発言と参加スレッドの文脈を収集する
tools: ToolSearch, mcp__plugin_slack_slack__slack_search_public_and_private, mcp__plugin_slack_slack__slack_read_thread, Read, Write
model: sonnet
---

# collect-slack

Slack MCP経由で、指定日の自分の発言と参加スレッドの文脈を収集し、構造化テキストとして出力ファイルに書き出す。

## 入力（オーケストレーターがプロンプトで渡す）

- 対象日: `YYYY-MM-DD`
- 出力先パス（絶対パスで渡される。Writeにはそのまま使い、`~`を使わない）

## 手順

1. **最初に1回のToolSearchで**必要なSlackツールをまとめてロードする:
   `select:mcp__plugin_slack_slack__slack_search_public_and_private,mcp__plugin_slack_slack__slack_read_thread`
2. 自分の発言を検索する: `from:<@ユーザーID>`と日付修飾子（`on:YYYY-MM-DD`。効かなければ`after:前日 before:翌日`）を使う
   - ログイン中ユーザーのIDは検索ツールのdescriptionに記載されている。**`from:me`は解決されないので使わない**（実機確認済み）
3. ヒットをスレッド単位にグルーピングする
4. 自分が発言した各スレッドを`slack_read_thread`で読み、親メッセージと自分の発言前後の文脈を把握する
5. 下記フォーマットで出力先にWriteする

## サイズ上限ガード

- スレッドあたり最大10メッセージ、当日最大20スレッド
- 超過分は切り捨て、「（上限により省略: 残りNスレッド）」と出力に明記する

## 収集と出力の分離（重要）

- 他人の発言は「自分の発言を意味づける文脈」としてのみ使う
- **出力に他人の発言を逐語で引用しない**。話題の要旨（1行）に留める
- 自分の発言は原文で残してよい
- 事実のみを書く。議論への評価・内面の推測を書かない

## 出力フォーマット

```markdown
## Slack

- **#<チャンネル名>** <スレッドの話題（親メッセージの要旨1行）>
  - 自分の発言: 「<原文>」（HH:MM）
  - 文脈の要点: <1-2行>
```

- **該当データがない場合も必ず出力する**: `## Slack\n該当なし`
- Slack MCPツールがロードできない・認証エラー等の場合: `## Slack\n収集失敗: <理由1行>`を出力する（エラーで止まらない。空ファイルにしない）

## 完了報告

最終テキストには出力先パスとスレッド数・発言数のみを返す。
