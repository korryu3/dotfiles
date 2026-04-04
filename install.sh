#!/bin/bash
set -uo pipefail

PERSONAL=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --personal|-p) PERSONAL=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")/scripts" && pwd)" || { echo "scriptsディレクトリが見つかりません"; exit 1; }

echo "=============================="
echo "  dotfiles setup"
echo "=============================="
echo ""

# Homebrew
if ! command -v brew &>/dev/null; then
  echo "=== Homebrewをインストール ==="
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || { echo "Homebrewのインストールに失敗しました"; exit 1; }
  eval "$(/opt/homebrew/bin/brew shellenv)" || { echo "brew shellenvの設定に失敗しました"; exit 1; }
  echo ""
fi

FAILURES=()

run_step() {
  local name="$1"
  shift
  if ! "$@"; then
    FAILURES+=("$name")
  fi
}

# brew bundle
echo "=== パッケージインストール ==="
echo ""
run_step "brew bundle (Brewfile)" brew bundle --file="$(dirname "$0")/Brewfile"

if [[ "$PERSONAL" == true ]]; then
  run_step "brew bundle (Brewfile.personal)" brew bundle --file="$(dirname "$0")/Brewfile.personal"
fi

echo ""
run_step "link.sh" "$SCRIPT_DIR/link.sh"
echo ""
run_step "binaries.sh" "$SCRIPT_DIR/binaries.sh"
echo ""
run_step "setup.sh" "$SCRIPT_DIR/setup.sh"
echo ""
run_step "completions.sh" "$SCRIPT_DIR/completions.sh"
echo ""
run_step "macos.sh" "$SCRIPT_DIR/macos.sh"

# サマリー
echo ""
echo "=============================="
if [[ ${#FAILURES[@]} -gt 0 ]]; then
  echo "  以下のステップが失敗しました:"
  for f in "${FAILURES[@]}"; do
    echo "    - $f"
  done
  echo "=============================="
  exit 1
else
  echo "  すべてのセットアップが完了しました"
  echo "=============================="
fi
