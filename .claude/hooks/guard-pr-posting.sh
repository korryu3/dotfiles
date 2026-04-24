#!/bin/bash
#
# PreToolUse hook: 他人のPRへのコメント投稿をブロックする
# 対象: gh pr comment, gh pr review, gh api .../pulls/.../reviews
# - 自分のPRならOK (exit 0)
# - 他人のPRならブロック (exit 2 + stderr)
#

# gh/jqコマンドが存在しなければスキップ
if ! command -v gh &>/dev/null || ! command -v jq &>/dev/null; then
  exit 0
fi

# stdinからJSON入力を読み取る
input=$(cat)
COMMAND=$(echo "$input" | jq -r '.tool_input.command // empty' 2>/dev/null) || exit 0

# --help等の情報取得系はスキップ
if [[ "$COMMAND" == *"--help"* || "$COMMAND" == *"-h"* ]]; then
  exit 0
fi

# 対象コマンドの判定とPR番号抽出
PR_REF=""
GH_CMD=""

if [[ "$COMMAND" == *"gh pr comment"* ]]; then
  GH_CMD="gh pr comment"
  PR_REF=$(echo "$COMMAND" | sed -n "s/.*gh pr comment[[:space:]]\{1,\}\([^[:space:]-][^[:space:]]*\).*/\1/p")
elif [[ "$COMMAND" == *"gh pr review"* ]]; then
  GH_CMD="gh pr review"
  PR_REF=$(echo "$COMMAND" | sed -n "s/.*gh pr review[[:space:]]\{1,\}\([^[:space:]-][^[:space:]]*\).*/\1/p")
elif [[ "$COMMAND" =~ gh\ api.*repos/([^/]+)/([^/]+)/pulls/([0-9]+)/(reviews|comments) ]]; then
  # GETリクエスト（読み取り）はスキップ。--method指定なしのデフォルトはGET
  if [[ "$COMMAND" != *"--method POST"* && "$COMMAND" != *"--method PATCH"* && "$COMMAND" != *"-X POST"* && "$COMMAND" != *"-X PATCH"* ]]; then
    exit 0
  fi
  GH_CMD="gh api (PR review/comment)"
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
  PR_NUM="${BASH_REMATCH[3]}"
  PR_AUTHOR=$(gh pr view "$PR_NUM" --repo "$OWNER/$REPO" --json author --jq '.author.login' 2>/dev/null) || true
else
  # 対象外のコマンドはスキップ
  exit 0
fi

# 自分のGitHubユーザー名を取得
MY_USER=$(gh api user --jq '.login' 2>/dev/null) || true
if [[ -z "$MY_USER" ]]; then
  echo "gh api userに失敗しました。${GH_CMD}をブロックします。" >&2
  exit 2
fi

# PR authorを取得（gh api経由でまだ取得していない場合）
if [[ -z "$PR_AUTHOR" ]]; then
  if [[ -n "$PR_REF" ]]; then
    PR_AUTHOR=$(gh pr view "$PR_REF" --json author --jq '.author.login' 2>/dev/null) || true
  else
    # PR番号なし = カレントブランチのPR
    PR_AUTHOR=$(gh pr view --json author --jq '.author.login' 2>/dev/null) || true
  fi
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
