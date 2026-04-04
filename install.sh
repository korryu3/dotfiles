#!/bin/bash
set -euo pipefail

PERSONAL=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --personal|-p) PERSONAL=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")/scripts" && pwd)"

echo "=============================="
echo "  dotfiles setup"
echo "=============================="
echo ""

# Homebrew
if ! command -v brew &>/dev/null; then
  echo "=== Homebrewをインストール ==="
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
  echo ""
fi

# brew bundle
echo "=== パッケージインストール ==="
echo ""
brew bundle --file="$(dirname "$0")/Brewfile"

if [[ "$PERSONAL" == true ]]; then
  brew bundle --file="$(dirname "$0")/Brewfile.personal"
fi

echo ""
"$SCRIPT_DIR/link.sh"
echo ""
"$SCRIPT_DIR/binaries.sh"
echo ""
"$SCRIPT_DIR/setup.sh"
echo ""
"$SCRIPT_DIR/completions.sh"
echo ""
"$SCRIPT_DIR/macos.sh"
