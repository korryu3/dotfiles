
############################
# 分割ファイルを読み込む様にする
source ${HOME}/.zsh/basic.zsh

############################



# 
setopt no_nomatch

# 日本語の文字化け防止
export LANG=ja_JP.UTF-8


# ----------------------------------------------------------------------------------------
# branch名を表示させるメソッドの設定

# function rprompt-git-current-branch {
#   local branch_name st branch_status

#   if [ ! -e  ".git" ]; then
#     # gitで管理されていないディレクトリは何も返さない
#     return
#   fi
#   branch_name=`git rev-parse --abbrev-ref HEAD 2> /dev/null`
#   st=`git status 2> /dev/null`
#   if [[ -n `echo "$st" | grep "^nothing to"` ]]; then
#     # 全てコミットされてクリーンな状態
#     branch_status="%F{192}"
#   elif [[ -n `echo "$st" | grep "^Untracked files"` ]]; then
#     # gitに管理されていないファイルがある状態
#     branch_status="%F{yellow}!"
#   elif [[ -n `echo "$st" | grep "^Changes not staged for commit"` ]]; then
#     # git addされていないファイルがある状態
#     branch_status="%F{red}*"
#   elif [[ -n `echo "$st" | grep "^Changes to be committed"` ]]; then
#     # git commitされていないファイルがある状態
#     branch_status="%F{red}+"
#   elif [[ -n `echo "$st" | grep "^rebase in progress"` ]]; then
#     # コンフリクトが起こった状態
#     echo "%F{198}!!"
#     return
#   else
#     # 上記以外の状態の場合は青色で表示させる
#     branch_status=""
#   fi
#   # ブランチ名を色付きで表示する
#   echo "${branch_status}[$branch_name]"
# }


# ----------------------------------------------------------------------------------------

# # promptの設定
# PROMPT='''  `rprompt-git-current-branch`
# %F{cyan}%~%f %F{magenta}%B〉%b%f'''
# PROMPT='%F{green}%m@%n%f %F{cyan}%~%f$ '

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
# zsh-completions(補完機能)の設定
# ----------------------------------------------------------------------------------------
# if [ -e /usr/local/share/zsh-completions ]; then
#     fpath=(/usr/local/share/zsh-completions $fpath)
# fi
# autoload -U compinit
# compinit -u


# コマンド実行後に1行空ける
add_newline() {
    if [[ -z $PS1_NEWLINE_LOGIN ]]; then
        PS1_NEWLINE_LOGIN=true
    else
        printf '\n'
    fi
}



# ----------------------------------------------------------------------------------------
# Alias
# ----------------------------------------------------------------------------------------
# Linux
alias ll="ls -l"

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



# >>> Hyper >>>

# Override auto-title when static titles are desired ($ title My new title)
title() { export TITLE_OVERRIDDEN=1; echo -en "\e]0;$*\a"}
# Turn off static titles ($ autotitle)
autotitle() { export TITLE_OVERRIDDEN=0 }; autotitle
# Condition checking if title is overridden
overridden() { [[ $TITLE_OVERRIDDEN == 1 ]]; }
# Echo asterisk if git state is dirty
gitDirty() { [[ $(git status 2> /dev/null | grep -o '\w\+' | tail -n1) != ("clean"|"") ]] && echo "*" }

# Show cwd when shell prompts for input.
precmd() {
   if overridden; then return; fi
   cwd=${$(pwd)##*/} # Extract current working dir only
#    cwd=${$(pwd)} # Extract current working dir
   print -Pn "\e]0;$cwd$(gitDirty)\a" # Replace with $pwd to show full path

    add_newline 
}

# Prepend command (w/o arguments) to cwd while waiting for command to complete.
preexec() {
   if overridden; then return; fi
   printf "\033]0;%s\a" "${1%% *} | $cwd$(gitDirty)" # Omit construct from $1 to show args
}

# <<< Hyper <<<



# >>> Azure CLI >>>

# autoload bashcompinit && bashcompinit
# source $(brew --prefix)/etc/bash_completion.d/az

# <<< Azure CLI <<<


# >>> .zfuncの補完ファイルを読み込む >>>
export FPATH="$FPATH:$HOME/.zfunc"
# <<< Poetry <<<


# >>> Homebrewの補完ファイルを読み込む >>>
export FPATH="/opt/homebrew/share/zsh/site-functions:$FPATH"
# <<<  <<<

# >>> zsh-abbrの補完 >>>
export FPATH="$(brew --prefix)/share/zsh-abbr:$FPATH"
# <<< zsh-abbr <<<


# 補完を有効にする
# 初期設定
autoload -Uz compinit
compinit


# >>> Anaconda3 >>>
# export PATH="/opt/homebrew/anaconda3/bin:$PATH"  # commented out by conda initialize
# <<< Anaconda3 <<<


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

# >>> zsh-abbr >>>
source $(brew --prefix)/share/zsh-abbr/zsh-abbr.zsh
# <<< zsh-abbr <<<

# >>> volta >>>
export PATH="$HOME/.volta/bin:$PATH"

# make
export PATH="/opt/homebrew/opt/make/libexec/gnubin:$PATH"

# bison
export PATH="/opt/homebrew/opt/bison/bin:$PATH"

# uv
eval "$(uv generate-shell-completion zsh)"

# pyenv
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# PHP pkg-config
# libiconv
export LIBICONV_PREFIX="$(brew --prefix libiconv)"
export CPPFLAGS="-I$LIBICONV_PREFIX/include ${CPPFLAGS}"
export LDFLAGS="-L$LIBICONV_PREFIX/lib ${LDFLAGS}"
export PKG_CONFIG_PATH="$LIBICONV_PREFIX/lib/pkgconfig:${PKG_CONFIG_PATH}"
# openssl
export OPENSSL_PREFIX="$(brew --prefix openssl@3)"
export PKG_CONFIG_PATH="$OPENSSL_PREFIX/lib/pkgconfig"
export CPPFLAGS="-I$OPENSSL_PREFIX/include"
export LDFLAGS="-L$OPENSSL_PREFIX/lib"
export PHP_BUILD_CONFIGURE_OPTS="--with-openssl=$OPENSSL_PREFIX"

# tkinter
# tkinterPath="/opt/homebrew/opt/tcl-tk"
# export PATH="$tkinterPath/bin:$PATH"
# export LDFLAGS="-L$tkinterPath/lib"
# export CPPFLAGS="-I$tkinterPath/include"
# export PKG_CONFIG_PATH="$tkinterPath/lib/pkgconfig"

# PATHとFPATHの重複を削除する
export PATH=$(echo $PATH | tr ':' '\n' | awk '!a[$0]++' | paste -sd: -)
export FPATH=$(echo $FPATH | tr ':' '\n' | awk '!a[$0]++' | paste -sd: -)


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

# Added by Antigravity
export PATH="$HOME/.antigravity/antigravity/bin:$PATH"

# Added by ClaudeCode
export PATH="$HOME/.local/bin:$PATH"

# マシン固有設定の読み込み
[[ -f ~/.zshrc.local ]] && source ~/.zshrc.local
