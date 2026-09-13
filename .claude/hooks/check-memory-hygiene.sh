#!/bin/bash
set -u

cat > /dev/null

# Claude Codeのprojects配下のディレクトリ名は、cwdの "/" と "." をどちらも "-" に置換したもの。
# "/" だけを置換していたため、ドットを含むパスでは
# ディレクトリが見つからず、以下の検査がすべて無言で素通りしていた。
# 変換規則が将来変わっても片方が当たるよう、候補を順に試す。
cwd="$(pwd)"
slug_slash_only="${cwd//\//-}"
slug="${slug_slash_only//./-}"

memory_dir=""
for candidate in "$slug" "$slug_slash_only"; do
  if [ -d "$HOME/.claude/projects/${candidate}/memory" ]; then
    memory_dir="$HOME/.claude/projects/${candidate}/memory"
    break
  fi
done

# どの候補にも無い場合は、メモリ未作成の新規プロジェクトと区別できないので無言で終える
if [ -z "$memory_dir" ]; then
  exit 0
fi

warnings=""

# --- type: project のメモリファイルを検出 ---
project_type_files=""
for f in "$memory_dir"/*.md; do
  [ -f "$f" ] || continue
  basename_f="$(basename "$f")"
  [ "$basename_f" = "MEMORY.md" ] && continue

  if head -30 "$f" | grep -qE '^\s*type:\s*project\s*$'; then
    project_type_files="${project_type_files}${project_type_files:+, }${basename_f}"
  fi
done

if [ -n "$project_type_files" ]; then
  warnings="${warnings}[不変層原則違反] type: project のメモリが存在します: ${project_type_files}。メモリにはタスク状態を書かず、notes/active-tasks.md に移行してください。\n"
fi

# --- ファイル数の閾値超過を検出 ---
threshold=15
count=0
for f in "$memory_dir"/*.md; do
  [ -f "$f" ] || continue
  [ "$(basename "$f")" = "MEMORY.md" ] && continue
  count=$((count + 1))
done

if [ "$count" -gt "$threshold" ]; then
  warnings="${warnings}[メモリ肥大化] メモリファイルが${count}件あります（閾値: ${threshold}件）。棚卸しして安定した知見はCLAUDE.md/AGENTS.md/rulesへ昇格させてください。\n"
fi

# --- 警告をhookSpecificOutputとして出力 ---
if [ -n "$warnings" ]; then
  formatted=$(printf '%b' "$warnings")
  json_escaped=$(printf '%s' "$formatted" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":%s}}' "$json_escaped"
fi

exit 0
