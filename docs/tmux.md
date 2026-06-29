# tmux チートシート

prefix: `C-a`

## セッション

| 操作 | キー |
|---|---|
| 新規セッション | `tmux new -s <name>` |
| デタッチ | `prefix d` |
| セッション一覧 | `tmux ls` |
| アタッチ | `tmux a -t <name>` |
| セッション切替 | `prefix s` |
| セッション名変更 | `prefix $` |

## ウィンドウ

| 操作 | キー |
|---|---|
| 新規ウィンドウ | `prefix c` |
| 次のウィンドウ | `prefix n` |
| 前のウィンドウ | `prefix p` |
| 番号で移動 | `prefix <1-9>` |
| ウィンドウ名変更 | `prefix ,` |
| ウィンドウ閉じる | `prefix &` |
| ウィンドウ一覧 | `prefix w` |

## ペイン

| 操作 | キー |
|---|---|
| 縦分割 | `prefix \|` |
| 横分割 | `prefix -` |
| ペイン移動 | `C-h/j/k/l` (prefix不要、nvimと共通) |
| ペインリサイズ | `prefix H/J/K/L` (5セル単位) |
| ペイン閉じる | `prefix x` |
| ペインズーム | `prefix z` |
| レイアウト切替 | `prefix Space` |

## コピーモード (vi)

| 操作 | キー |
|---|---|
| コピーモード開始 | `prefix [` |
| 選択開始 | `v` |
| コピー(+クリップボード) | `y` |
| キャンセル | `Escape` |
| 検索 | `/` |
| ペースト | `prefix ]` |

## その他

| 操作 | キー |
|---|---|
| 設定リロード | `prefix r` |
| 画面クリア | `prefix C-l` |
| コマンドモード | `prefix :` |
| キー一覧 | `prefix ?` |

## 注意

- `C-l`（画面クリア）はペイン移動に使われるため、`prefix C-l`で代替
- nvim内の`C-h/j/k/l`はvim-tmux-navigatorがnvim splitとtmux paneをシームレスに接続
