#!/bin/bash
set -u

INPUT=$(cat)
TOOL_NAME=$(printf '%s' "$INPUT" | jq -r '.tool_name // ""')

[ "$TOOL_NAME" = "Bash" ] || exit 0

COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // ""')

printf '%s' "$COMMAND" | grep -qE '(^|[;&|]\s*)gh(\s|$)' || exit 0

GH_TOKEN=$(gh auth token 2>/dev/null) || {
  echo "[inject-gh-token] gh auth token failed" >&2
  exit 0
}

[ -n "$GH_TOKEN" ] || exit 0

TMPFILE="/tmp/.claude-gh-token"
printf '%s' "$GH_TOKEN" > "$TMPFILE"
chmod 600 "$TMPFILE"

jq -n \
  --arg cmd "GH_TOKEN=\$(cat ${TMPFILE}) ${COMMAND}" \
  '{
    "suppressOutput": true,
    "hookSpecificOutput": {
      "hookEventName": "PreToolUse",
      "permissionDecision": "allow",
      "updatedInput": {
        "command": $cmd
      }
    }
  }'

exit 0
