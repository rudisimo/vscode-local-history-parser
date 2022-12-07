#!/usr/bin/env bash
#-------------------------------------------------------------------------------------------------------------
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the MIT License. See LICENSE.txt for license information.
#-------------------------------------------------------------------------------------------------------------
set -Eeuo pipefail

# TODO: remove debugging statement
printenv | sort

# Enforce execution by root user
if [ "$(id -u)" -ne 0 ]; then
    echo >&2 "ERROR: Script must be run as root. Use sudo, su, or add 'USER root' to your Dockerfile before running this script."
    exit 1
fi

##########################################################
# Pre-install
##########################################################

# Feature options with defaults
OPT_DEBUG=${DEBUG_FEATURES:-""}
OPT_USERNAME=${USERNAME:-"automatic"}
OPT_UID=${USER_UID:-"automatic"}
OPT_GID=${USER_GID:-"automatic"}
OPT_SHELL=${USER_SHELL:-"bash"}
OPT_VOLUMES=${USER_VOLUMES:-""}

# Enable debugging mode
if [ -n "${OPT_DEBUG}" ]; then
    set -x
fi

##########################################################
# Non-Root user configuration
##########################################################

# If in automatic mode, determine if a user already exists, if not use vscode
if [ "${OPT_USERNAME}" = "automatic" ]; then
    OPT_USERNAME=""
    POSSIBLE_USERS=("vscode" "$(awk -v val=1000 -F ":" '$3==val{print $1}' /etc/passwd)")
    for CURRENT_USER in "${POSSIBLE_USERS[@]}"; do
        if id -u "${CURRENT_USER}" > /dev/null 2>&1; then
            OPT_USERNAME="${CURRENT_USER}"
            break
        fi
    done
    if [ "${OPT_USERNAME}" = "" ]; then
        OPT_USERNAME="vscode"
    fi
elif [ "${OPT_USERNAME}" = "disabled" ]; then
    OPT_USERNAME="root"
fi

# Create or update a non-root user to match UID/GID.
if [ "${OPT_USERNAME}" != "root" ]; then
    # Update existing user/group
    if id -u ${OPT_USERNAME} > /dev/null 2>&1; then
        echo >&2 "INFO: Updating existing user: ${OPT_USERNAME}"
        if [ "${OPT_GID}" != "automatic" ] && [ "${OPT_GID}" != "$(id -g ${OPT_USERNAME})" ]; then
            groupmod --gid $OPT_GID "$(id -gn $OPT_USERNAME)"
            usermod --gid $OPT_GID $OPT_USERNAME
        fi
        if [ "${OPT_UID}" != "automatic" ] && [ "${OPT_UID}" != "$(id -u ${OPT_USERNAME})" ]; then
            usermod --uid $OPT_UID $OPT_USERNAME
        fi
    # Create new user/group
    else
        echo >&2 "INFO: Creating new user: ${OPT_USERNAME}"
        if [ "${OPT_GID}" = "automatic" ]; then
            groupadd $OPT_USERNAME
        else
            groupadd --gid $OPT_GID $OPT_USERNAME
        fi
        if [ "${OPT_UID}" = "automatic" ]; then
            useradd --gid $OPT_USERNAME -m $OPT_USERNAME
        else
            useradd --uid $OPT_UID --gid $OPT_USERNAME -m $OPT_USERNAME
        fi
    fi

    # Add sudo support for non-root user
    echo "${OPT_USERNAME} ALL=(root) NOPASSWD:ALL" | tee "/etc/sudoers.d/${OPT_USERNAME}" >/dev/null
    chmod 0440 "/etc/sudoers.d/${OPT_USERNAME}"
    usermod -aG sudo,root ${OPT_USERNAME}
fi

##########################################################
# Shell configuration
##########################################################

# Configure default shell
if [ -n "${OPT_SHELL}" ]; then
    USER_SHELL=$(command -v ${OPT_SHELL} 2>/dev/null)
    if [ -n "${USER_SHELL}" ]; then
        echo >&2 "INFO: Configuring shell: ${USER_SHELL}"
        usermod -s $USER_SHELL $OPT_USERNAME

        # Create marker
        SHELL_ALREADY_SET="${OPT_USERNAME}"
    fi
fi

# Configure volume mounts
if [ -n "${OPT_VOLUMES}" ]; then
    for VOLUME_MOUNT in ${OPT_VOLUMES//$'\s'/$IFS}; do
        if [ -n "${VOLUME_MOUNT}" ]; then
            echo >&2 "INFO: Creating volume mount: ${VOLUME_MOUNT}"
            runuser -l "${OPT_USERNAME}" -c "mkdir -p ${VOLUME_MOUNT}"
        fi
    done
fi

# Configure home directory
if [ "${OPT_USERNAME}" = "root" ]; then
    USER_RC_PATH="/root"
else
    USER_RC_PATH="/home/${OPT_USERNAME}"
fi

# Configure Zsh (move to a dedicated file)
cat /dev/null > "${USER_RC_PATH}/.zshrc"
runuser -l "${OPT_USERNAME}" -c "mkdir -p ${USER_RC_PATH}/.config/{fzf,zsh}"
runuser -l "${OPT_USERNAME}" -c "curl -fsSL 'https://github.com/ohmyzsh/ohmyzsh/raw/master/lib/compfix.zsh' -o ${USER_RC_PATH}/.config/zsh/compfix.zsh"
runuser -l "${OPT_USERNAME}" -c "curl -fsSL 'https://github.com/ohmyzsh/ohmyzsh/raw/master/lib/completion.zsh' -o ${USER_RC_PATH}/.config/zsh/completion.zsh"
runuser -l "${OPT_USERNAME}" -c "curl -fsSL 'https://github.com/ohmyzsh/ohmyzsh/raw/master/lib/directories.zsh' -o ${USER_RC_PATH}/.config/zsh/directories.zsh"
runuser -l "${OPT_USERNAME}" -c "curl -fsSL 'https://github.com/ohmyzsh/ohmyzsh/raw/master/lib/git.zsh' -o ${USER_RC_PATH}/.config/zsh/git.zsh"
runuser -l "${OPT_USERNAME}" -c "curl -fsSL 'https://github.com/ohmyzsh/ohmyzsh/raw/master/lib/history.zsh' -o ${USER_RC_PATH}/.config/zsh/history.zsh"
runuser -l "${OPT_USERNAME}" -c "curl -fsSL 'https://github.com/ohmyzsh/ohmyzsh/raw/master/lib/theme-and-appearance.zsh' -o ${USER_RC_PATH}/.config/zsh/theme-and-appearance.zsh"
runuser -l "${OPT_USERNAME}" -c "curl -fsSL 'https://github.com/ohmyzsh/ohmyzsh/raw/master/lib/vcs_info.zsh' -o ${USER_RC_PATH}/.config/zsh/vcs_info.zsh"
runuser -l "${OPT_USERNAME}" -c "curl -fsSL 'https://github.com/caiogondim/bullet-train.zsh/raw/master/bullet-train.zsh-theme' -o ${USER_RC_PATH}/.config/zsh/bullet-train.zsh-theme"
runuser -l "${OPT_USERNAME}" -c "curl -fsSL 'https://github.com/junegunn/fzf/raw/0.32.1/shell/completion.zsh' -o ${USER_RC_PATH}/.config/fzf/completion.zsh"
runuser -l "${OPT_USERNAME}" -c "curl -fsSL 'https://github.com/junegunn/fzf/raw/0.32.1/shell/key-bindings.zsh' -o ${USER_RC_PATH}/.config/fzf/key-bindings.zsh"
cat <<EOF >${USER_RC_PATH}/.zshrc
autoload -Uz compaudit compinit zrecompile
setopt magicequalsubst nonomatch notify numericglobsort promptsubst

HISTFILE="\${HOME}/.local/share/zsh/zsh-history"
HIST_STAMPS="yyyy-mm-dd"
DISABLE_UNTRACKED_FILES_DIRTY="true"

export PATH="\${HOME}/.local/bin:\${PATH}"
export LANG="en_US.UTF-8"
export LC_ALL="en_US.UTF-8"
export AWS_PAGER=""
export EDITOR="code -w"
export MANPAGER="less -X"

# zsh
source "\${HOME}/.config/zsh/compfix.zsh" 2>/dev/null
source "\${HOME}/.config/zsh/completion.zsh" 2>/dev/null
source "\${HOME}/.config/zsh/directories.zsh" 2>/dev/null
source "\${HOME}/.config/zsh/git.zsh" 2>/dev/null
source "\${HOME}/.config/zsh/history.zsh" 2>/dev/null
source "\${HOME}/.config/zsh/theme-and-appearance.zsh" 2>/dev/null
source "\${HOME}/.config/zsh/vcs_info.zsh" 2>/dev/null

# aliases
alias find="rg --files --hidden --follow --no-ignore-vcs -g '!{node_modules,.git}'"

# theme
BULLETTRAIN_CUSTOM_MSG="arcos"
BULLETTRAIN_PROMPT_ORDER=(custom dir virtualenv aws git)
source "\${HOME}/.config/zsh/bullet-train.zsh-theme" 2>/dev/null

# fzf
[[ \$- == *i* ]] && source "\${HOME}/.config/fzf/completion.zsh" 2>/dev/null
source "\${HOME}/.config/fzf/key-bindings.zsh" 2>/dev/null
EOF
# echo "eval \"\$(pyenv init -)\"" | tee -a "${USER_RC_PATH}/.zshrc"
# echo "eval \"\$(nodenv init -)\"" | tee -a "${USER_RC_PATH}/.zshrc"
# echo "eval \"\$(rbenv init -)\"" | tee -a "${USER_RC_PATH}/.zshrc"
chown -R ${OPT_USERNAME}:${OPT_USERNAME} "${USER_RC_PATH}"

##########################################################
# Post-install
##########################################################

# TBD