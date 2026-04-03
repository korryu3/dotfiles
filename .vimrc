
"#####表示設定#####
set number "行番号を表示する
"行番号の色指定
highlight lineNr ctermfg=247  
set title "編集中のファイル名を表示
set showmatch "括弧入力時の対応する括弧を表示
syntax on "コードの色分け
set tabstop=4 "インデントをスペース4つ分に設定
"オートインデント
set smartindent 
"バッファ内で扱う文字コード(文字列)
set encoding=utf-8
"書き込む文字コード(文字列) : この場合encodingと同じなので省略可
set fileencoding=utf-8
"読み込む文字コード(文字列のリスト) : この場合UTF-8を試し、だめならShift_JIS
set fileencodings=utf-8,cp932

"#####検索設定#####
set ignorecase "大文字/小文字の区別なく検索する
set smartcase "検索文字列に大文字が含まれている場合は区別して検索する
set wrapscan "検索時に最後まで行ったら最初に戻る
set rtp+=/opt/homebrew/opt/fzf  "vimの検索にfzfを使う
