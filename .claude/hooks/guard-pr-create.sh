#!/bin/bash
#
# PreToolUse hook: gh pr createはdraftで作り、ユーザーをアサインさせる
#

COMMAND=$(jq -r '.tool_input.command // empty' 2>/dev/null) || exit 0

[[ "$COMMAND" =~ (^|[^[:alnum:]_./-])gh[[:space:]]+pr[[:space:]]+create([[:space:]]|$) ]] || exit 0

missing=()
[[ "$COMMAND" =~ (^|[[:space:]])(--draft|-d)([[:space:]]|$) ]] || missing+=("--draft")
[[ "$COMMAND" =~ (^|[[:space:]])(--assignee|-a)([[:space:]=]|$) ]] || missing+=("--assignee @me")

if (( ${#missing[@]} > 0 )); then
  echo "PRはdraftで作り、ユーザーをアサインする。不足: ${missing[*]}" >&2
  exit 2
fi
exit 0
