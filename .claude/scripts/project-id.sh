#!/bin/bash
# worktreeやサブディレクトリから実行しても、メインのチェックアウトのルートでIDを作る
common=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
if [ "$(basename "$common")" = ".git" ]; then
  root=$(dirname "$common")
else
  root=$(git rev-parse --show-toplevel 2>/dev/null) || root=$PWD
fi
echo "${root//\//-}"
