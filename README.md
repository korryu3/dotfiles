# dotfiles

## Setup

```bash
# 1. Clone
git clone https://github.com/KorRyu3/dotfiles.git ~/dotfiles

# 2. Brew packages
brew bundle --file=~/dotfiles/Brewfile

# 3. Symlinks
cd ~/dotfiles && ./install.sh
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
