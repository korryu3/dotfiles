# dotfiles

## Setup

```bash
# 1. Clone
git clone https://github.com/KorRyu3/dotfiles.git ~/dotfiles

# 2. Install (Homebrew導入 → パッケージ → シンボリックリンク → セットアップ)
cd ~/dotfiles && ./install.sh

# 3. Brewfileにないパッケージを削除 (任意)
brew bundle cleanup --file=~/dotfiles/Brewfile
brew bundle cleanup --file=~/dotfiles/Brewfile --force  # 実際に削除
```

## SSH config (manual)

```
Host github.com
  HostName github.com
  AddKeysToAgent yes
  UseKeychain yes
  User git
  Port 22
  IdentityFile {YOUR_PRIVATE_KEY_PATH}
```

## TODO

- [ ] macOS system defaults (Dock, Finder, key repeat etc.)
- [ ] Nix Home Manager migration
- [ ] VSCode Settings Sync
- [ ] Serena config (`~/.serena/serena_config.yml`) の管理（`projects` リストがPC固有で自動更新されるため要検討）
