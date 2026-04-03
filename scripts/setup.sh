#!/bin/bash
set -euo pipefail

echo "=== ツール初期化 ==="
echo ""

# Rust (via rustup-init)
if command -v rustup-init &>/dev/null; then
  if [[ -f "$HOME/.cargo/env" ]]; then
    echo "  Rust: インストール済み"
  else
    echo "  Rust をインストール中..."
    rustup-init -y
  fi
else
  echo "  スキップ (rustup未インストール): Rust"
fi

# Node.js (via volta)
if command -v volta &>/dev/null; then
  if volta list node 2>/dev/null | grep -q default; then
    echo "  Node.js (volta): インストール済み"
  else
    echo "  Node.js をインストール中..."
    volta install node
  fi
else
  echo "  スキップ (volta未インストール): Node.js"
fi

# Python (via uv)
if command -v uv &>/dev/null; then
  if uv python list --only-installed 2>/dev/null | grep -q .; then
    echo "  Python (uv): インストール済み"
  else
    echo "  Python をインストール中..."
    uv python install --default --preview-features python-install-default
  fi
else
  echo "  スキップ (uv未インストール): Python"
fi

echo ""
echo "完了!"
