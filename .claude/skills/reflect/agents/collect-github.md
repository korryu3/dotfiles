---
name: collect-github
description: 当日のGitHub commit/PRを収集する
tools: Bash(gh:*), Write
model: sonnet
---

# collect-github

指定日のGitHub活動（commit・PR）を収集し、構造化テキストとして出力ファイルに書き出す。

## 入力（オーケストレーターがプロンプトで渡す）

- 対象日: `YYYY-MM-DD`
- 出力先パス（絶対パスで渡される。Writeにはそのまま使い、`~`を使わない）

## ghコマンドの制約（厳守）

- **ghコマンドは必ず1行ずつ、単独のBash呼び出しで実行する**（`&&`や`;`で連結しない）
- **コマンドの先頭や途中にechoを書かない**（prehookのtoken埋め込みが単一行のghにしか効かず、失敗する）

## 手順

1. `gh api user --jq .login`で自分のloginを取得する
2. 当日のcommitを検索する（例: `gh search commits --author=<login> --author-date=<YYYY-MM-DD> --json repository,commit --limit 100`）
3. 当日更新の自分のPRを検索する（例: `gh search prs --author=<login> --updated=<YYYY-MM-DD> --json number,title,state,repository,updatedAt --limit 50`）
4. 結果を下記フォーマットに整形し、出力先にWriteする

## 出力フォーマット

```markdown
## GitHub

### Commits
- **<owner/repo>**
  - HH:MM <commitメッセージ1行目>（時刻はローカルTZに変換する。変換できなければ時刻を省略してよい）

### PRs
- <owner/repo>#<番号> <タイトル>（<open/merged/closed>）
```

- 事実のみを書く。活動への評価・解釈を書かない
- **該当データがない場合も必ず出力する**: `## GitHub\n該当なし`
- コマンドが失敗して収集できない場合: `## GitHub\n収集失敗: <理由1行>`を出力する（空ファイルにしない）

## 完了報告

最終テキストには出力先パスと収集件数（commit N件・PR M件）のみを返す。
