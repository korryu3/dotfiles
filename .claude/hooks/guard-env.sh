#!/bin/bash
# Block Bash commands that reference .env files containing secrets.
# Invoked as PreToolUse hook for the Bash tool. Stdin is the tool-use JSON.
# Safe variants ending in .example / .sample / .template are allowed.
#
# Note: The Read tool blocks all .env* files via permissions.deny (Read(**/*.env*)),
# so Claude cannot read .env.example with the Read tool. Bash (cat/echo/etc.) however
# passes the permission layer and reaches this hook, where the template allowlist
# above lets templates through. So Claude can still read or write template files
# (e.g. `cat .env.example`, `echo FOO=bar > .env.example`) via Bash if needed.

set -u

cmd=$(jq -r '.tool_input.command // ""' 2>/dev/null || printf '')

unsafe=$(
  printf '%s' "$cmd" \
    | grep -oE '\.env[A-Za-z0-9._-]*' \
    | grep -vE '\.(example|sample|template)$' \
    | head -5 \
    || true
)

if [ -n "${unsafe:-}" ]; then
  refs=$(printf '%s' "$unsafe" | tr '\n' ' ')
  printf 'blocked: .env file access detected (%s)\n' "$refs" >&2
  exit 2
fi

exit 0
