#!/bin/bash
set -euo pipefail

echo "=== macOS設定 ==="
echo ""

# ---------------------------------------------------------------------------
# NSGlobalDomain
# ---------------------------------------------------------------------------
echo "--- NSGlobalDomain ---"

defaults write NSGlobalDomain AppleLanguages -array "en-JP" "ja-JP"
echo "  言語優先順位: English, 日本語"

defaults write NSGlobalDomain AppleShowAllExtensions -bool true
echo "  全拡張子表示: ON"

defaults write NSGlobalDomain AppleInterfaceStyleSwitchesAutomatically -bool true
echo "  ダークモード自動切替: ON"

defaults write NSGlobalDomain com.apple.keyboard.fnState -bool true
echo "  fnキーをファンクションキーに: ON"

defaults write NSGlobalDomain com.apple.sound.beep.volume -float 0
echo "  ビープ音量: 0"

defaults write NSGlobalDomain AppleMiniaturizeOnDoubleClick -bool false
echo "  ダブルクリック最小化: OFF"

defaults write NSGlobalDomain com.apple.mouse.scaling -float 3
echo "  マウス速度: 3"

defaults write NSGlobalDomain com.apple.trackpad.scaling -float 3
echo "  トラックパッド速度: 3"

defaults write NSGlobalDomain KeyRepeat -int 2
echo "  キーリピート速度: 2"

defaults write NSGlobalDomain InitialKeyRepeat -int 15
echo "  キーリピート開始遅延: 15"

defaults write NSGlobalDomain AppleKeyboardUIMode -int 3
echo "  Tab全UIフォーカス: ON"

defaults write NSGlobalDomain ApplePressAndHoldEnabled -bool false
echo "  長押しアクセント: OFF"

defaults write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false
echo "  自動スペル修正: OFF"

defaults write NSGlobalDomain NSAutomaticCapitalizationEnabled -bool false
echo "  自動大文字化: OFF"

defaults write NSGlobalDomain NSAutomaticDashSubstitutionEnabled -bool false
echo "  自動ダッシュ置換: OFF"

defaults write NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false
echo "  自動引用符置換: OFF"

defaults write NSGlobalDomain NSAutomaticPeriodSubstitutionEnabled -bool false
echo "  自動ピリオド置換: OFF"

defaults write NSGlobalDomain NSDocumentSaveNewDocumentsToCloud -bool false
echo "  iCloudデフォルト保存: OFF"

echo ""

# ---------------------------------------------------------------------------
# Dock
# ---------------------------------------------------------------------------
echo "--- Dock ---"

defaults write com.apple.dock autohide -bool true
echo "  自動非表示: ON"

defaults write com.apple.dock tilesize -int 128
echo "  Dockサイズ: 128"

defaults write com.apple.dock mru-spaces -bool false
echo "  Spaces自動並べ替え: OFF"

defaults write com.apple.dock showAppExposeGestureEnabled -bool true
echo "  アプリExpose: ON"

defaults write com.apple.dock wvous-br-corner -int 14
echo "  ホットコーナー右下: クイックノート"

defaults write com.apple.dock autohide-delay -float 0
echo "  表示遅延: 0"

defaults write com.apple.dock show-recents -bool false
echo "  最近使ったアプリ: OFF"

defaults write com.apple.dock mineffect -string "scale"
echo "  ミニマイズエフェクト: scale"

echo ""

# ---------------------------------------------------------------------------
# Finder
# ---------------------------------------------------------------------------
echo "--- Finder ---"

defaults write com.apple.finder FXPreferredViewStyle -string "clmv"
echo "  デフォルト表示: カラム"

defaults write com.apple.finder ShowHardDrivesOnDesktop -bool false
echo "  デスクトップにHDD表示: OFF"

defaults write com.apple.finder ShowPathbar -bool true
echo "  パスバー: ON"

defaults write com.apple.finder ShowStatusBar -bool true
echo "  ステータスバー: ON"

defaults write com.apple.finder AppleShowAllFiles -bool true
echo "  隠しファイル表示: ON"

defaults write com.apple.finder FXEnableExtensionChangeWarning -bool false
echo "  拡張子変更警告: OFF"

defaults write com.apple.finder FXDefaultSearchScope -string "SCcf"
echo "  検索範囲: カレントフォルダ"

echo ""

# ---------------------------------------------------------------------------
# スクリーンキャプチャ
# ---------------------------------------------------------------------------
echo "--- スクリーンキャプチャ ---"

mkdir -p "${HOME}/Documents/screenshot"

defaults write com.apple.screencapture location -string "${HOME}/Documents/screenshot"
echo "  保存先: ~/Documents/screenshot"

defaults write com.apple.screencapture disable-shadow -bool true
echo "  ウィンドウ影: OFF"

echo ""

# ---------------------------------------------------------------------------
# トラックパッド
# ---------------------------------------------------------------------------
echo "--- トラックパッド ---"

defaults write com.apple.AppleMultitouchTrackpad Clicking -bool true
echo "  タップでクリック: ON"

defaults write com.apple.AppleMultitouchTrackpad TrackpadThreeFingerDrag -bool true
echo "  3本指ドラッグ: ON"

echo ""

# ---------------------------------------------------------------------------
# メニューバー
# ---------------------------------------------------------------------------
echo "--- メニューバー ---"

defaults write com.apple.menuextra.clock ShowSeconds -bool true
echo "  時計の秒表示: ON"

defaults write com.apple.menuextra.battery ShowPercent -string "YES"
echo "  バッテリー残量%: ON"

echo ""

# ---------------------------------------------------------------------------
# デスクトップサービス
# ---------------------------------------------------------------------------
echo "--- デスクトップサービス ---"

defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
echo "  ネットワーク上に.DS_Store作成: OFF"

defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true
echo "  USB上に.DS_Store作成: OFF"

echo ""

# ---------------------------------------------------------------------------
# クラッシュレポーター
# ---------------------------------------------------------------------------
echo "--- クラッシュレポーター ---"

defaults write com.apple.CrashReporter DialogType -string "notification"
echo "  レポート表示: 通知"

echo ""

# ---------------------------------------------------------------------------
# プリント
# ---------------------------------------------------------------------------
echo "--- プリント ---"

defaults write com.apple.print.PrintingPrefs "Quit When Finished" -bool true
echo "  印刷完了後に終了: ON"

echo ""

# ---------------------------------------------------------------------------
# アクティビティモニタ
# ---------------------------------------------------------------------------
echo "--- アクティビティモニタ ---"

defaults write com.apple.ActivityMonitor ShowCategory -int 0
echo "  表示カテゴリ: すべてのプロセス"

echo ""

# ---------------------------------------------------------------------------
# 設定反映
# ---------------------------------------------------------------------------
echo "=== 設定反映 ==="
echo ""

killall Finder 2>/dev/null || true
echo "  Finder を再起動しました"

killall Dock 2>/dev/null || true
echo "  Dock を再起動しました"

echo ""
echo "完了!"
