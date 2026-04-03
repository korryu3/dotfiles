
############################
# 基本設定の読み込み
############################


# ビープ音を鳴らさない
setopt nolistbeep

# コマンドのスペルミスを指摘する
setopt correct

# 諸々のパスを通す
export PATH="/usr/local/bin:$PATH"

# 履歴ファイルを明示
HISTFILE=~/.zsh_history

# タブ補完などを有効にする
autoload -Uz compinit && compinit

# cdしたらls -1(縦表示)を同時に実行する
# chpwd() {ls -1}


# completion & suggestion
if type brew &>/dev/null; then
  FPATH=$(brew --prefix)/share/zsh-completions:$FPATH
  source $(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh
fi


# ls
export LSCOLORS=gxfxcxdxbxegedabagacag
export LS_COLORS='di=36;40:ln=35;40:so=32;40:pi=33;40:ex=31;40:bd=34;46:cd=34;43:su=30;41:sg=30;46:tw=30;42:ow=30;46'

# lsがカラー表示になるようエイリアスを設定
case "${OSTYPE}" in
darwin*)
  # Mac
  alias ls="ls -GF"
  ;;
esac


# 補完候補に色つける
autoload -U colors
colors
zstyle ':completion:*' list-colors "${LS_COLORS}"


# nodebrew
# export PATH=/usr/local/var/nodebrew/current/bin:$PATH




# zsh syntax highlighting
source $(brew --prefix)/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
typeset -A ZSH_HIGHLIGHT_STYLES

# pathの下線を消す
ZSH_HIGHLIGHT_STYLES[path]="none"  # "none" -> "underline"


# 諸々の色などを設定

# ZSH_HIGHLIGHTING_HIGHLIGHTERS=(main brackets cursor url)
# ZSH_HIGHLIGHT_STYLES[precommand]='fg=190,bold'
# ZSH_HIGHLIGHT_STYLES[command]='fg=190'
# ZSH_HIGHLIGHT_STYLES[builtin]='fg=178'


# ZSH_HIGHLIGHTING_HIGHLIGHTERS=(main brackets cursor)
# ZSH_HIGHLIGHT_STYLES[precommand]=''
# ZSH_HIGHLIGHT_STYLES[command]=''
# ZSH_HIGHLIGHT_STYLES[builtin]=''
