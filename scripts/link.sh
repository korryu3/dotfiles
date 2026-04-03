#!/bin/bash
set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HOME_DIR="$HOME"
BACKUP_DIR="$HOME/.dotfiles_backup/$(date +%Y-%m-%d_%H%M%S)"

# リンク対象ファイル: リポジトリ内の相対パス
FILES=(
  .zshrc
  .zshenv
  .zprofile
  .zsh
  .gitconfig
  .vimrc
  .config/starship.toml
  .config/ghostty/config
  .config/alacritty/alacritty.toml
  .config/alacritty/keybindings.toml
  .config/mise/config.toml
  .config/git/ignore
  .tmux.conf
  .colima/default/colima.yaml
  .codex/config.toml
  .claude/settings.json
  .claude/CLAUDE.md
  .claude/statusline.py
  .claude/rules
  .claude/agents
  .claude/skills
  .claude/scripts
)

link_file() {
  local src="$DOTFILES_DIR/$1"
  local dest="$HOME_DIR/$1"

  # ソースが存在しなければスキップ
  if [[ ! -e "$src" ]]; then
    echo "  スキップ (ソースなし): $1"
    return
  fi

  # 既に正しいリンクならスキップ
  if [[ -L "$dest" ]] && [[ "$(readlink "$dest")" == "$src" ]]; then
    echo "  リンク済み: $1"
    return
  fi

  # 親ディレクトリ作成
  mkdir -p "$(dirname "$dest")"

  # 既存ファイルがあればバックアップ
  if [[ -e "$dest" ]] || [[ -L "$dest" ]]; then
    local backup_path="$BACKUP_DIR/$1"
    mkdir -p "$(dirname "$backup_path")"
    mv "$dest" "$backup_path"
    echo "  バックアップ: $1 → $BACKUP_DIR/$1"
  fi

  ln -s "$src" "$dest"
  echo "  リンク作成: $1"
}

# dotfilesを指す壊れたシンボリックリンクを削除
echo "=== 壊れたリンクの掃除 ==="
echo ""

find "$HOME_DIR" -maxdepth 5 -type l 2>/dev/null | while read -r link; do
  target=$(readlink "$link")
  if [[ "$target" == "$DOTFILES_DIR/"* ]] && [[ ! -e "$link" ]]; then
    echo "  壊れたリンク削除: $link"
    rm "$link"
  fi
done || true

echo ""
echo "=== シンボリックリンク作成 ==="
echo ""

for file in "${FILES[@]}"; do
  link_file "$file"
done

echo ""
echo "完了!"
