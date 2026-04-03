
############################
# 分割ファイルを読み込む様にする
source ${HOME}/.zsh/basic.zsh
typeset -U path fpath

############################

setopt no_nomatch

# 日本語の文字化け防止
export LANG=ja_JP.UTF-8

# historyのsize
export HISTSIZE=100000
export SAVEHIST=100000
export HISTFILE=~/.zsh_history

# プロンプトが表示されるたび、毎回プロンプトの文字列を評価し、置換する
setopt prompt_subst

# プロンプト複数起動時のhistory共有
setopt share_history

# 履歴を追記モードで書き込む（過去の履歴を消さない）
setopt append_history
# コマンド実行のたびに即座に履歴ファイルに書き込む
setopt inc_append_history

# 重複するコマンドのhistory削除
setopt hist_ignore_all_dups

# 単語の入力途中でもTab補完を有効化
setopt complete_in_word

# 補完候補をハイライト
zstyle ':completion:*:default' menu select=1

# キャッシュの利用による補完の高速化
zstyle ':completion::complete:*' use-cache true

# 大文字、小文字を区別せず補完する
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'

# 補完リストの表示間隔を狭くする
setopt list_packed

# 補完に関するオプション
# http://voidy21.hatenablog.jp/entry/20090902/1251918174
setopt auto_param_slash      # ディレクトリ名の補完で末尾の / を自動的に付加し、次の補完に備える
setopt mark_dirs             # ファイル名の展開でディレクトリにマッチした場合 末尾に / を付加


# ----------------------------------------------------------------------------------------
# Alias
# ----------------------------------------------------------------------------------------
# Editor
alias c="code ."

# Git
gacpfunc() {
	git commit -am "$*"
	git push origin HEAD
}
alias gb="git branch"
alias gb-d="git branch -d"
alias gsi="git switch"
alias gs="git status"
alias ga="git add"
alias gc="git commit"
alias gp="git push"
alias gacp=gacpfunc
alias gf="git fetch"
alias gpl="git pull"
alias gl="git log --oneline"
alias gres="git restore"
alias gres-s="git restore --staged"
alias gd="git diff"
alias gd-s="git diff --staged"
alias gmom="git merge origin main"
alias gsid='git switch $(git remote show origin | grep "HEAD branch" | awk "{print \$NF}")'

# Docker
alias d="docker"
alias dcm="docker-compose"

# Terraform
alias tf="terraform"

# Homebrew
alias bi="brew install"
alias bi-c="brew install --cask"
alias bl="brew list"
alias bu="brew upgrade"
alias bup="brew update"

# act
alias act="act --container-architecture linux/amd64"


# ----------------------------------------------------------------------------------------


# >>> Homebrew用のパス優先度 >>>
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
# <<< Homebrew用のパス優先度 <<<


# >>> .zfuncの補完ファイルを読み込む >>>
export FPATH="$FPATH:$HOME/.zfunc"
# <<< Poetry <<<


# >>> Homebrewの補完ファイルを読み込む >>>
export FPATH="/opt/homebrew/share/zsh/site-functions:$FPATH"
# <<<  <<<


# 補完を有効にする
# 初期設定
autoload -Uz compinit
compinit


# >>> mise (programing laguages version manager) >>>
export PATH="$HOME/.local/share/mise/shims:$PATH"
eval "$(/opt/homebrew/opt/mise/bin/mise activate zsh)"
# <<< mise <<<


# >>> Starship >>>
eval "$(starship init zsh)"
# <<< Starship <<<

# >>> zoxide (smart cd) >>>
eval "$(zoxide init zsh)"
# <<< zoxide <<<

# >>> volta >>>
export PATH="$HOME/.volta/bin:$PATH"

# make
export PATH="/opt/homebrew/opt/make/libexec/gnubin:$PATH"

# uv
eval "$(uv generate-shell-completion zsh)"

# 履歴をGUIで検索できるようにする# fzf history
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
    # sed で先頭の「数字＋空白」を削除し、純粋なコマンドのみを抽出
    BUFFER=$(echo "$selected" | sed 's/^[ ]*[0-9]\+[ ]*//')
    CURSOR=${#BUFFER}
    zle reset-prompt
  fi
}

zle -N fzf-select-history
bindkey '^H' fzf-select-history

autoload -U +X bashcompinit && bashcompinit

# Terraform
complete -o nospace -C /opt/homebrew/bin/terraform terraform

# Added by ClaudeCode
export PATH="$HOME/.local/bin:$PATH"

# マシン固有設定の読み込み
[[ -f ~/.zshrc.local ]] && source ~/.zshrc.local
