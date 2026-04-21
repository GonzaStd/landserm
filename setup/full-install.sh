#!/bin/bash
set -euo pipefail

# Full installer for Landserm
# - Clones or updates the repository into /opt/landserm
# - Runs setup/install.sh (which requires root and checks its location)
# This script is intended to be safe when piped from curl, and will
# re-exec itself with sudo if necessary.

REPO_URL="https://github.com/GonzaStd/landserm.git"
BRANCH="main"
DEST="/opt/landserm"

echo "=== Landserm full-install.sh ==="

# If not root, try to re-run the same URL with sudo
if [ "$(id -u)" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
        echo "Not running as root — re-running the installer with sudo..."
        exec sudo bash -c "curl -fsSL https://raw.githubusercontent.com/GonzaStd/landserm/refs/heads/main/setup/full-install.sh | bash"
    else
        echo "This installer must be run as root. Please re-run with sudo or as root."
        exit 1
    fi
fi

# Prepare a temporary directory
TMPDIR=$(mktemp -d)
trap 'rm -rf "${TMPDIR}"' EXIT

# Backup existing non-git installation or update if it's a git repo
if [ -d "${DEST}" ]; then
    if [ -d "${DEST}/.git" ]; then
        echo "Existing git checkout found in ${DEST} — updating to latest ${BRANCH}..."
        # Ensure we fetch latest state and reset
        if command -v git >/dev/null 2>&1; then
            git -C "${DEST}" fetch --all --prune
            git -C "${DEST}" reset --hard "origin/${BRANCH}" || true
            git -C "${DEST}" clean -fdx || true
        else
            echo "git not available, backing up existing folder and re-cloning..."
            mv "${DEST}" "${DEST}.backup.$(date +%s)"
        fi
    else
        echo "Non-git folder already exists at ${DEST} — moving it to a backup location"
        mv "${DEST}" "${DEST}.backup.$(date +%s)"
    fi
fi

# Clone or extract the repository
if [ ! -d "${DEST}" ]; then
    if command -v git >/dev/null 2>&1; then
        echo "Cloning ${REPO_URL} (branch: ${BRANCH}) into ${DEST}..."
        git clone --depth 1 --branch "${BRANCH}" "${REPO_URL}" "${DEST}"
    else
        echo "git not found. Downloading tarball and extracting..."
        TARFILE="${TMPDIR}/repo.tar.gz"
        curl -L "https://codeload.github.com/GonzaStd/landserm/tar.gz/${BRANCH}" -o "${TARFILE}"
        mkdir -p "${TMPDIR}/extract"
        tar -xzf "${TARFILE}" -C "${TMPDIR}/extract"
        mv "${TMPDIR}/extract/landserm-${BRANCH}" "${DEST}"
    fi
fi

# Ensure the destination exists now
if [ ! -d "${DEST}" ]; then
    echo "Failed to fetch the repository into ${DEST}. Exiting." >&2
    exit 2
fi

cd "${DEST}"

echo "Running the packaged installer: /bin/bash setup/install.sh"
/bin/bash setup/install.sh

echo "=== Full installation finished ==="
exit 0

