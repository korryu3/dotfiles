#!/bin/bash
set -euo pipefail

echo "=== バイナリインストール ==="
echo ""

# Claude Code
if ! command -v claude &>/dev/null; then
  echo "  Claude Code をインストール中..."
  curl -fsSL https://claude.ai/install.sh | bash
else
  echo "  Claude Code: インストール済み"
fi

echo ""
echo "完了!"
