#!/bin/bash
#
# PreToolUse hook: 他人のPRへの gh pr comment / gh pr review をブロックする
# - 自分のPRならOK (exit 0)
# - 他人のPRならブロック (exit 2 + stderr)
#

# gh/jqコマンドが存在しなければスキップ（ghがない環境ではgh pr comment/reviewも実行不可）
if ! command -v gh &>/dev/null || ! command -v jq &>/dev/null; then
  exit 0
fi

# stdinからJSON入力を読み取る
input=$(cat)
COMMAND=$(echo "$input" | jq -r '.tool_input.command // empty' 2>/dev/null) || exit 0

# gh pr comment / gh pr review を含まないコマンドはスキップ
if [[ "$COMMAND" != *"gh pr comment"* && "$COMMAND" != *"gh pr review"* ]]; then
  exit 0
fi

# --help等の情報取得系はスキップ
if [[ "$COMMAND" == *"--help"* || "$COMMAND" == *"-h"* ]]; then
  exit 0
fi

# マッチしたコマンド名を特定（エラーメッセージ用）
if [[ "$COMMAND" == *"gh pr comment"* ]]; then
  GH_CMD="gh pr comment"
else
  GH_CMD="gh pr review"
fi

# 自分のGitHubユーザー名を取得
MY_USER=$(gh api user --jq '.login' 2>/dev/null) || true
if [[ -z "$MY_USER" ]]; then
  echo "gh api userに失敗しました。${GH_CMD}をブロックします。" >&2
  exit 2
fi

# コマンドからPR番号/URLを抽出
PR_REF=$(echo "$COMMAND" | sed -n "s/.*${GH_CMD}[[:space:]]\{1,\}\([^[:space:]-][^[:space:]]*\).*/\1/p")

# PR authorを取得
if [[ -n "$PR_REF" ]]; then
  PR_AUTHOR=$(gh pr view "$PR_REF" --json author --jq '.author.login' 2>/dev/null) || true
else
  # PR番号なし = カレントブランチのPRにコメント
  PR_AUTHOR=$(gh pr view --json author --jq '.author.login' 2>/dev/null) || true
fi

if [[ -z "$PR_AUTHOR" ]]; then
  echo "PR authorの取得に失敗しました。${GH_CMD}をブロックします。" >&2
  exit 2
fi

# 自分のPRならOK
if [[ "$PR_AUTHOR" == "$MY_USER" ]]; then
  exit 0
fi

# 他人のPRならブロック
echo "他人のPR (author: $PR_AUTHOR, you: $MY_USER) への${GH_CMD}をブロックしました。" >&2
exit 2
