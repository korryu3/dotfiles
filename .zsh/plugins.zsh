# 見た目・プラグイン設定

# LS_COLORS
export LS_COLORS='di=36;40:ln=35;40:so=32;40:pi=33;40:ex=31;40:bd=34;46:cd=34;43:su=30;41:sg=30;46:tw=30;42:ow=30;46'
autoload -U colors && colors
zstyle ':completion:*' list-colors "${LS_COLORS}"

# zsh plugins
local _plugins=(
  "${HOMEBREW_PREFIX}/share/zsh-autosuggestions/zsh-autosuggestions.zsh"
  "${HOMEBREW_PREFIX}/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
)
for p in "${_plugins[@]}"; do
  [[ -f "$p" ]] && source "$p"
done
typeset -A ZSH_HIGHLIGHT_STYLES
ZSH_HIGHLIGHT_STYLES[path]="none"
