ARG VARIANT="bullseye-slim"
FROM public.ecr.aws/debian/debian:${VARIANT} as builder

LABEL org.opencontainers.image.source="https://github.com/rudisimo/devcontainers"
LABEL org.opencontainers.image.licenses="MIT"

SHELL ["/bin/bash", "-c"]

####################################################################################
# Configure OS
####################################################################################

ARG DEBIAN_FRONTEND=noninteractive

# Install APT packages
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lib,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,id=debconf,target=/var/cache/debconf,sharing=locked \
    set -eux \
    && apt-get -y update -qq \
    && apt-get -y install -qq -o=Dpkg::Use-Pty=0 --no-install-recommends \
        apt-utils \
        make \
        build-essential \
        ca-certificates \
        less \
        vim \
        wget \
        curl \
        tar \
        zip \
        unzip \
        gnupg2 \
        git \
        zsh \
        sudo \
        tree \
        htop \
        procps \
        locales \
        xz-utils \
        openssh-client

# Configure UTF-8 locale
RUN set -eux \
    && if ! grep -Eo '^\s*en_US.UTF-8\s+UTF-8' /etc/locale.gen >/dev/null; then \
        echo "en_US.UTF-8 UTF-8" | tee -a /etc/locale.gen >/dev/null \
        && locale-gen \
    ; fi

####################################################################################
# Configure pyenv
####################################################################################
FROM builder as pyenv
####################################################################################

# Install Python dependencies
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lib,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,id=debconf,target=/var/cache/debconf,sharing=locked \
    set -eux \
    && apt-get -y update -qq \
    && apt-get -y install -qq -o=Dpkg::Use-Pty=0 --no-install-recommends \
        llvm \
        tk-dev \
        libssl-dev \
        zlib1g-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        libncursesw5-dev \
        libxml2-dev \
        libxmlsec1-dev \
        libffi-dev \
        liblzma-dev

# Install pyenv tool
ARG PYENV_BRANCH="master"
ARG PYENV_ROOT="/usr/local/pyenv"
RUN set -eux \
    && mkdir -p ${PYENV_ROOT}/plugins/{pyenv-doctor,pyenv-virtualenv,pyenv-which-ext} \
    && curl -fsSL "https://github.com/pyenv/pyenv/archive/refs/heads/${PYENV_BRANCH}.tar.gz" | tar -xzvf - -C ${PYENV_ROOT} --strip-components=1 --warning=no-unknown-keyword --no-same-owner \
    && curl -fsSL "https://github.com/pyenv/pyenv-doctor/archive/refs/heads/${PYENV_BRANCH}.tar.gz" | tar -xzvf - -C ${PYENV_ROOT}/plugins/pyenv-doctor --warning=no-unknown-keyword --no-same-owner \
    && curl -fsSL "https://github.com/pyenv/pyenv-virtualenv/archive/refs/heads/${PYENV_BRANCH}.tar.gz" | tar -xzvf - -C ${PYENV_ROOT}/plugins/pyenv-virtualenv --warning=no-unknown-keyword --no-same-owner \
    && curl -fsSL "https://github.com/pyenv/pyenv-which-ext/archive/refs/heads/${PYENV_BRANCH}.tar.gz" | tar -xzvf - -C ${PYENV_ROOT}/plugins/pyenv-which-ext --warning=no-unknown-keyword --no-same-owner
ENV PATH=${PYENV_ROOT}/bin:${PATH}
ENV PYENV_ROOT=${PYENV_ROOT}

####################################################################################
# Configure environment + miscellaneous tools + packages
####################################################################################
FROM pyenv as features
####################################################################################

# Install Gitflow (AVH)
ARG GITFLOW_BRANCH="develop"
ARG GITFLOW_VERSION="stable"
ARG GITFLOW_PREFIX="/usr/local/gitflow"
ARG WITH_GITFLOW="y"
RUN set -eux \
    && if [ "gitflow-${WITH_GITFLOW}" = "gitflow-y" ]; then \
        curl -fsSL "https://raw.githubusercontent.com/petervanderdoes/gitflow-avh/${GITFLOW_BRANCH}/contrib/gitflow-installer.sh" -o /tmp/gitflow-installer.sh \
        && env REPO_NAME=${GITFLOW_PREFIX} bash /tmp/gitflow-installer.sh install "${GITFLOW_VERSION}" \
        && rm -rf /tmp/gitflow-installer.sh ${GITFLOW_PREFIX}/.git \
    ; fi

# Install Python (pyenv)
ARG PYTHON_VERSION="latest"
COPY feature-configure-python/* /tmp/build-python-feature/
RUN --mount=type=cache,id=pip-cache,target=/root/.cache/pip,sharing=locked \
    set -eux \
    && env PYTHON_DEPS="$(tr -s '\n' ' ' < /tmp/build-python-feature/requirements.txt)" bash -x /tmp/build-python-feature/install.sh

# Install extra Python dependencies
ARG PYTHON_DEPS=""
RUN --mount=type=cache,id=pip-cache,target=/root/.cache/pip,sharing=locked \
    set -eux \
    && env PYTHON_VERSION="" bash -x /tmp/build-python-feature/install.sh
RUN rm -rf /tmp/build-python-feature

# Configure user
ARG USERNAME="vscode"
ARG USER_SHELL="bash"
ARG USER_VOLUMES=""
COPY feature-configure-user/* /tmp/build-user-feature/
RUN set -eux \
    && bash -x /tmp/build-user-feature/install.sh \
    && rm -rf /tmp/build-user-feature

# Install extra APT packages
ARG APT_PACKAGES=""
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lib,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,id=debconf,target=/var/cache/debconf,sharing=locked \
    set -eux \
    && if [ -n "${APT_PACKAGES}" ]; then \
        apt-get -y update -qq \
        && apt-get -y install -qq -o=Dpkg::Use-Pty=0 --no-install-recommends \
            ${APT_PACKAGES} \
    ; fi
