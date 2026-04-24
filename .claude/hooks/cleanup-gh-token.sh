#!/bin/bash
set -u

INPUT=$(cat)
TOOL_NAME=$(printf '%s' "$INPUT" | jq -r '.tool_name // ""')

[ "$TOOL_NAME" = "Bash" ] || exit 0

rm -f /tmp/.claude-gh-token

exit 0
