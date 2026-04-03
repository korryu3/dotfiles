#!/bin/bash
set -euo pipefail

echo "=== 補完ファイル生成 ==="
echo ""

mkdir -p "$HOME/.zfunc"

# rustup
if command -v rustup &>/dev/null; then
  rustup completions zsh > "$HOME/.zfunc/_rustup"
  echo "  生成: ~/.zfunc/_rustup"
else
  echo "  スキップ (rustup未インストール): _rustup"
fi

echo ""
echo "完了!"
