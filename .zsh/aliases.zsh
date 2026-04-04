# eza (ls replacement)
alias ls="eza --icons --git"
alias ll="eza --icons --git -l"
alias la="eza --icons --git -la"
alias lt="eza --icons --git --tree --level=2"

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
