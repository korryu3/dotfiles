
############################
# 基本設定の読み込み
############################


# ビープ音を鳴らさない
setopt nolistbeep

# コマンドのスペルミスを指摘する
setopt correct

# 諸々のパスを通す
export PATH="/usr/local/bin:$PATH"


# completion & suggestion
if type brew &>/dev/null; then
  FPATH=$(brew --prefix)/share/zsh-completions:$FPATH
  source $(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh
fi


# ls (eza)
alias ls="eza --icons --git"
alias ll="eza --icons --git -l"
alias la="eza --icons --git -la"
alias lt="eza --icons --git --tree --level=2"

# 補完候補に色つける
export LS_COLORS='di=36;40:ln=35;40:so=32;40:pi=33;40:ex=31;40:bd=34;46:cd=34;43:su=30;41:sg=30;46:tw=30;42:ow=30;46'
autoload -U colors
colors
zstyle ':completion:*' list-colors "${LS_COLORS}"


# zsh syntax highlighting
source $(brew --prefix)/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
typeset -A ZSH_HIGHLIGHT_STYLES

# pathの下線を消す
ZSH_HIGHLIGHT_STYLES[path]="none"  # "none" -> "underline"
