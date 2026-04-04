: ${HOMEBREW_PREFIX:=$(brew --prefix)}
source ${HOME}/.zsh/plugins.zsh
typeset -U path fpath

# setopt
setopt no_nomatch
setopt nolistbeep
setopt correct
setopt prompt_subst
setopt share_history
setopt append_history
setopt inc_append_history
setopt hist_ignore_all_dups
setopt complete_in_word
setopt list_packed
setopt auto_param_slash
setopt mark_dirs

# History
export HISTSIZE=100000
export SAVEHIST=100000
export HISTFILE=~/.zsh_history

# 補完
zstyle ':completion:*:default' menu select=1
zstyle ':completion::complete:*' use-cache true
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'

# PATH / FPATH
export FPATH="${HOMEBREW_PREFIX}/share/zsh/site-functions:${HOMEBREW_PREFIX}/share/zsh-completions:$FPATH"
export FPATH="$FPATH:$HOME/.zfunc"
export PATH="$HOME/.local/share/mise/shims:$PATH"
export PATH="$HOME/.volta/bin:$PATH"
export PATH="${HOMEBREW_PREFIX}/opt/make/libexec/gnubin:$PATH"
export PATH="$HOME/.local/bin:$PATH"

# compinit
autoload -Uz compinit
compinit

# Aliases
source ${HOME}/.zsh/aliases.zsh

# mise
eval "$(${HOMEBREW_PREFIX}/opt/mise/bin/mise activate zsh)"

# starship
eval "$(starship init zsh)"

# zoxide
eval "$(zoxide init zsh)"

# uv
eval "$(uv generate-shell-completion zsh)"

# bashcompinit + terraform
autoload -U +X bashcompinit && bashcompinit
complete -o nospace -C ${HOMEBREW_PREFIX}/bin/terraform terraform

# fzf history (Ctrl+H)
function fzf-select-history() {
  local history_lines selected
  history_lines=$(history -n -r 1 | awk '!a[$0]++')

  selected=$(echo "$history_lines" | fzf \
    --query "$LBUFFER" \
    --reverse \
    --height=40% \
    --border \
 )

  if [[ -n "$selected" ]]; then
    BUFFER=$(echo "$selected" | sed 's/^[ ]*[0-9]\+[ ]*//')
    CURSOR=${#BUFFER}
    zle reset-prompt
  fi
}

zle -N fzf-select-history
bindkey '^H' fzf-select-history

# マシン固有設定
[[ -f ~/.zshrc.local ]] && source ~/.zshrc.local
