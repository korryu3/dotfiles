#!/bin/bash
#
# PreToolUse hook: PRレビュー投稿系コマンドをガードする
# 対象: gh pr comment, gh pr review, gh api .../pulls/.../(reviews|comments), gh api graphql
# - submit系（pendingレビューの公開）はPR authorを問わずユーザーに確認 (ask)
# - PRレビュー系GraphQL mutationはPR authorを問わずユーザーに確認 (ask)
#   （node IDからのPR author解決はhook内では困難なため、自分/他人の判定をしない）
# - それ以外の書き込みは、自分のPRならOK (exit 0) / 他人のPRならユーザーに確認 (ask)
# - 判定不能ならブロック (permissionDecision: deny)
#

# gh/jqコマンドが存在しなければスキップ
if ! command -v gh &>/dev/null || ! command -v jq &>/dev/null; then
  exit 0
fi

# stdinからJSON入力を読み取る
input=$(cat)
COMMAND=$(echo "$input" | jq -r '.tool_input.command // empty' 2>/dev/null) || exit 0

# --help等の情報取得系はスキップ（-hは単語境界で判定。GraphQLのnode ID等が偶然含む文字列を誤検出しない）
if [[ "$COMMAND" == *"--help"* ]] || [[ "$COMMAND" =~ (^|[[:space:]])-h($|[[:space:]]) ]]; then
  exit 0
fi

ask() {
  jq -n --arg reason "$1" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "ask",
      permissionDecisionReason: $reason
    }
  }'
  exit 0
}

deny() {
  jq -n --arg reason "$1" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $reason
    }
  }'
  exit 0
}

# submit系はPR authorを問わず確認（pendingレビューが公開される操作）
if [[ "$COMMAND" =~ pulls/[^[:space:]/]+/reviews/[^[:space:]/]+/events ]] || [[ "$COMMAND" == *"submitPullRequestReview"* ]]; then
  ask "PRレビューのsubmit（pendingレビューの公開）です"
fi

# PRレビュー系GraphQL mutationはPR authorを問わず確認。
# author解決フローには合流させない（カレントブランチPRのauthorで誤判定されるため）
if [[ "$COMMAND" == *"gh api graphql"* ]]; then
  if [[ "$COMMAND" == *"addPullRequestReviewThread"* || "$COMMAND" == *"updatePullRequestReviewComment"* || "$COMMAND" == *"deletePullRequestReviewComment"* || "$COMMAND" == *"createPullRequestReview"* ]]; then
    ask "PRレビュー系のGraphQL mutationです"
  fi
  # その他のGraphQLは対象外
  exit 0
fi

# 対象コマンドの判定とPR番号抽出
PR_REF=""
GH_CMD=""
PR_AUTHOR=""
AUTHOR_RESOLVED=""

if [[ "$COMMAND" == *"gh pr comment"* ]]; then
  GH_CMD="gh pr comment"
  PR_REF=$(echo "$COMMAND" | sed -n "s/.*gh pr comment[[:space:]]\{1,\}\([^[:space:]-][^[:space:]]*\).*/\1/p")
elif [[ "$COMMAND" == *"gh pr review"* ]]; then
  GH_CMD="gh pr review"
  PR_REF=$(echo "$COMMAND" | sed -n "s/.*gh pr review[[:space:]]\{1,\}\([^[:space:]-][^[:space:]]*\).*/\1/p")
elif [[ "$COMMAND" =~ gh\ api.*repos/([^/]+)/([^/]+)/pulls/([0-9]+)/(reviews|comments) ]]; then
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
  PR_NUM="${BASH_REMATCH[3]}"
  # 書き込み判定: --method/-XのPOST/PATCH/DELETE/PUT、または--input（method省略でも書き込み）。
  # それ以外（GET相当）はスキップ
  WRITE=0
  for m in POST PATCH DELETE PUT; do
    if [[ "$COMMAND" == *"--method $m"* || "$COMMAND" == *"-X $m"* ]]; then
      WRITE=1
    fi
  done
  if [[ "$COMMAND" == *"--input"* ]]; then
    WRITE=1
  fi
  if [[ "$WRITE" == 0 ]]; then
    exit 0
  fi
  GH_CMD="gh api (PR review/comment)"
  # ghのプレースホルダ展開に委ねるため、gh api直接形でauthorを解決する
  # （{owner}/{repo}の文字どおり形でもカレントリポジトリで正しく展開される。
  #   gh pr view --repoはプレースホルダ形で失敗しカレントブランチPRへ誤フォールバックする）
  # gh apiは失敗時にエラーJSONをstdoutへ出すため、失敗時は必ず空に戻す
  PR_AUTHOR=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUM" --jq '.user.login' 2>/dev/null) || PR_AUTHOR=""
  AUTHOR_RESOLVED=1
else
  # 対象外のコマンドはスキップ
  exit 0
fi

# 自分のGitHubユーザー名を取得（gh apiは失敗時にエラーJSONをstdoutへ出すため、失敗時は必ず空に戻す）
MY_USER=$(gh api user --jq '.login' 2>/dev/null) || MY_USER=""
if [[ -z "$MY_USER" ]]; then
  deny "gh api userに失敗しました。${GH_CMD}をブロックします。"
fi

# PR authorを取得（gh pr comment / gh pr review分岐のみ。gh api分岐は解決済みのため
# カレントブランチPRへフォールバックさせない）
if [[ -z "$PR_AUTHOR" && -z "$AUTHOR_RESOLVED" ]]; then
  if [[ -n "$PR_REF" ]]; then
    PR_AUTHOR=$(gh pr view "$PR_REF" --json author --jq '.author.login' 2>/dev/null) || true
  else
    # PR番号なし = カレントブランチのPR
    PR_AUTHOR=$(gh pr view --json author --jq '.author.login' 2>/dev/null) || true
  fi
fi

if [[ -z "$PR_AUTHOR" ]]; then
  deny "PR authorの取得に失敗しました。${GH_CMD}をブロックします。"
fi

# 自分のPRならOK
if [[ "$PR_AUTHOR" == "$MY_USER" ]]; then
  exit 0
fi

# 他人のPRならユーザーに確認を求める
ask "他のユーザー(@${PR_AUTHOR})のPRへの${GH_CMD}です (you: @${MY_USER})"
