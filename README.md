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

## 手動設定が必要なアプリ

Sandbox制約により`defaults write`で設定できないアプリ:

- **Safari**: 設定 > 詳細 > スマート検索フィールド > 「Webサイトの完全なアドレスを表示」をON / 「Webデベロッパ用の機能を表示」をON
- **TextEdit**: 設定 > 「標準テキスト」を選択（リッチテキストではなくプレーンテキストをデフォルトに）

## 壁紙（Aerial Wallpaper）

1. Google Driveから`Aerial_Wallpaper/`を`~/Documents/`にコピー
2. システム設定 > 壁紙 > 「Add Folder or Album」から`~/Documents/Aerial_Wallpaper/`を追加
3. Shuffle: Every Day に設定

<details>
<summary>壁紙の作り方（既存Macから再作成する場合）</summary>

1. システム設定 > 壁紙 > 空撮から全てダウンロード
2. `/Library/Application Support/com.apple.idleassetsd/Customer/4KSDR240FPS/`からmovファイルを取得
3. ffmpegでフレーム切り出し
4. `~/Documents/Aerial_Wallpaper/`に配置

</details>

## TODO

- [x] macOS system defaults (Dock, Finder, key repeat etc.)
- [ ] Nix Home Manager migration
- [ ] VSCode Settings Sync
- [ ] Serena config (`~/.serena/serena_config.yml`) の管理（`projects` リストがPC固有で自動更新されるため要検討）
