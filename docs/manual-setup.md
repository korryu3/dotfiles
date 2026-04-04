# 手動セットアップ

`install.sh`で自動化できない設定をまとめたドキュメント。

## SSH config

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
