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

# Feature parameters configuration
OPT_DEBUG=${DEBUG_FEATURES:-""}
OPT_VERSION=${PYTHON_VERSION:-""}
OPT_INSTALL_DEPS=${PYTHON_DEPS:-""}

# Enable debugging mode
if [ -n "${OPT_DEBUG}" ]; then
    set -x
fi

build_version_filter() {
    local version=$1
    if [[ "${version}" =~ ^latest ]]; then
        filter="v3.*"
    elif [[ "${version}" =~ ^[0-9](\.[0-9]+)?$ ]]; then
        filter="v${version}.*"
    else
        filter="v${version}"
    fi
    echo $filter
}

find_version_from_git_tags() {
    local filter=$(build_version_filter "$1")
    local repository=${2:-"https://github.com/python/cpython"}
    local full_tag=$(git ls-remote --refs --tags --sort="v:refname" "${repository}" "${filter}" | grep -E '[[:digit:]]\.[[:digit:]]+\.[[:digit:]]+$' | tail -n 1 | awk '{ print $2 }')
    local full_version=$(echo ${full_tag} | sed 's;refs/tags/v;;')
    echo $full_version
}

##########################################################
# Install
##########################################################

# Install distribution globally
if [ -n "${OPT_VERSION}" ]; then
    # Find version to build
    VERSION=$(find_version_from_git_tags "${OPT_VERSION}")
    if [ -z "${VERSION}" ]; then
        echo >&2 "ERROR: Could generate a valid version from '${OPT_VERSION}'"
        exit 1
    fi

    # Build from source
    echo >&2 "INFO: Installing python ${VERSION}..."
    export PYTHON_CONFIGURE_OPTS="--enable-shared"
    $(pyenv which python-build) -v "${VERSION}" /usr/local

    # Upgrade package manager
    echo >&2 "INFO: Updating pip..."
    python3 -m pip install --disable-pip-version-check install --upgrade pip
fi

# Install extra packages
if [ -n "${OPT_INSTALL_DEPS}" ]; then
    for PACKAGE in ${OPT_INSTALL_DEPS//$'\s'/$IFS}; do
        echo >&2 "INFO: Installing dependency ${PACKAGE}..."
        python3 -m pip install --disable-pip-version-check install --upgrade "${PACKAGE}"
    done
fi

##########################################################
# Post-install
##########################################################

# TBD