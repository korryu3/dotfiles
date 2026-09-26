#!/bin/bash
set -u

INPUT=$(cat)
TOOL_NAME=$(printf '%s' "$INPUT" | jq -r '.tool_name // ""')

[ "$TOOL_NAME" = "Bash" ] || exit 0

COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // ""')

# gh が単語として現れる位置（行頭・空白・;&|(`の直後）を拾う。gh-pages や /path/gh は拾わない
printf '%s' "$COMMAND" | grep -qE '(^|[[:space:];&|(`])gh([[:space:]]|$)' || exit 0

GH_TOKEN=$(gh auth token 2>/dev/null) || {
  echo "[inject-gh-token] gh auth token failed" >&2
  exit 0
}

[ -n "$GH_TOKEN" ] || exit 0

# 呼び出しごとに別ファイルにし、並列実行や別セッションの後片付けと競合しないようにする
TOKEN_DIR="${CLAUDE_GH_TOKEN_DIR:-/tmp}"
TOOL_USE_ID=$(printf '%s' "$INPUT" | jq -r '.tool_use_id // ""' | tr -cd 'A-Za-z0-9_-')
[ -n "$TOOL_USE_ID" ] || exit 0
TMPFILE="${TOKEN_DIR}/.claude-gh-token-${TOOL_USE_ID}"

# PostToolUseが走らなかった呼び出しの取り残しを掃除する
find "$TOKEN_DIR" -maxdepth 1 -name '.claude-gh-token-*' -mmin +60 -delete 2>/dev/null

(umask 077 && printf '%s' "$GH_TOKEN" > "$TMPFILE")

# tokenはexportしないshell変数に置き、ghのshell関数経由でghのプロセスにだけ渡す。
# 前置代入と違い、複合コマンド・ループ・コマンド置換の中のghにも届く
# catはユーザーのshellでaliasされていることがあるので、commandで素のcatを呼ぶ
PREFIX="__claude_gh_token=\"\$(command cat '${TMPFILE}')\"; gh() { GH_TOKEN=\"\$__claude_gh_token\" command gh \"\$@\"; };"

# updatedInputは入力全体を置き換えるので、元のtool_inputにcommandだけを上書きする。
# permissionDecisionは返さず、実行の可否は通常の判定に任せる
printf '%s' "$INPUT" | jq \
  --arg cmd "${PREFIX} ${COMMAND}" \
  '{
    "suppressOutput": true,
    "hookSpecificOutput": {
      "hookEventName": "PreToolUse",
      "updatedInput": (.tool_input + {"command": $cmd})
    }
  }'

exit 0
