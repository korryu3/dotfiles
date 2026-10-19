#!/bin/bash
#
# PreToolUse hook: Monitorのcommandでghを使わせない
# ghのtoken注入hook（inject-gh-token.sh）はBashツールにしか効かず、Monitorの中では認証が通らないため。
#

COMMAND=$(jq -r '.tool_input.command // empty' 2>/dev/null) || exit 0

if [[ "$COMMAND" =~ (^|[^[:alnum:]_./-])gh([[:space:]]|$) ]]; then
  echo "Monitorの中ではghを使えない（token注入hookがBashにしか効かず認証が通らない）。Bashのrun_in_backgroundでポーリングするか、ユーザーに確認すること。" >&2
  exit 2
fi
exit 0
