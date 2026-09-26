#!/bin/bash
set -u

INPUT=$(cat)
TOOL_NAME=$(printf '%s' "$INPUT" | jq -r '.tool_name // ""')

[ "$TOOL_NAME" = "Bash" ] || exit 0

# inject-gh-token.shがこの呼び出し用に作ったファイルだけを消す
TOKEN_DIR="${CLAUDE_GH_TOKEN_DIR:-/tmp}"
TOOL_USE_ID=$(printf '%s' "$INPUT" | jq -r '.tool_use_id // ""' | tr -cd 'A-Za-z0-9_-')
[ -n "$TOOL_USE_ID" ] || exit 0

TMPFILE="${TOKEN_DIR}/.claude-gh-token-${TOOL_USE_ID}"

# バックグラウンド実行ではPostToolUseが起動直後に走り、コマンドがtokenを読む前に消してしまう。
# その場合は消すのを遅らせる（取り残しはinject-gh-token.shの1時間の掃除でも拾う）
BACKGROUND=$(printf '%s' "$INPUT" | jq -r '.tool_input.run_in_background // false')
if [ "$BACKGROUND" = "true" ]; then
  (sleep 60; rm -f "$TMPFILE") >/dev/null 2>&1 &
  exit 0
fi

rm -f "$TMPFILE"

exit 0
