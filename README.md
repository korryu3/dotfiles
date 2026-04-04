# dotfiles

![Zsh](https://img.shields.io/badge/-Zsh-000?style=flat-square&logo=zsh)
![Neovim](https://img.shields.io/badge/-Neovim-57A143?style=flat-square&logo=neovim&logoColor=white)
![Ghostty](https://img.shields.io/badge/-Ghostty-333?style=flat-square&logo=ghostty&logoColor=white)
![Starship](https://img.shields.io/badge/-Starship-DD0B78?style=flat-square&logo=starship&logoColor=white)
![Homebrew](https://img.shields.io/badge/-Homebrew-FBB040?style=flat-square&logo=homebrew&logoColor=black)
![macOS](https://img.shields.io/badge/-macOS-000?style=flat-square&logo=apple&logoColor=white)

## Setup

```bash
# 1. Clone
git clone https://github.com/korryu3/dotfiles.git ~/dotfiles

# 2. Install (Homebrew導入 → パッケージ → シンボリックリンク → セットアップ → macOS設定)
cd ~/dotfiles && ./install.sh

# 個人用パッケージも含める場合
cd ~/dotfiles && ./install.sh --personal

# 3Dパッケージ (colmap, rtabmap, cloudcompare) も含める場合
cd ~/dotfiles && ./install.sh --3d

# 3. Brewfileにないパッケージを削除 (任意)
brew bundle cleanup --file=~/dotfiles/Brewfile
brew bundle cleanup --file=~/dotfiles/Brewfile --force  # 実際に削除
```

## Manual Setup

`install.sh`で自動化できない設定は[docs/manual-setup.md](docs/manual-setup.md)を参照。

## TODO

- [x] macOS system defaults (Dock, Finder, key repeat etc.)
- [ ] Nix Home Manager migration
- [ ] VSCode Settings Sync
- [ ] Serena config (`~/.serena/serena_config.yml`) の管理（`projects` リストがPC固有で自動更新されるため要検討）
