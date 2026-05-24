#!/bin/bash
# Automated GitHub CLI setup for Claude Code sessions
# This script runs on SessionStart to ensure gh CLI is available and authenticated

set -e

GH_VERSION="2.83.1"

# Add common binary locations to PATH
export PATH="$HOME/.local/bin:$HOME/bin:/usr/local/bin:$PATH"

# Check if gh is already installed
if command -v gh &> /dev/null; then
    echo "[gh] CLI found at $(which gh)"
else
    echo "[gh] CLI not found, installing..."

    # Detect platform
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    [ "$ARCH" = "x86_64" ] && ARCH="amd64"
    [ "$ARCH" = "aarch64" ] && ARCH="arm64"

    echo "[gh] Detected platform: ${OS}_${ARCH}"

    echo "[gh] Version: ${GH_VERSION}"

    # Build download URL based on platform
    if [ "$OS" = "darwin" ]; then
        ARCHIVE_NAME="gh_${GH_VERSION}_macOS_${ARCH}.zip"
        ARCHIVE_EXT="zip"
    else
        ARCHIVE_NAME="gh_${GH_VERSION}_${OS}_${ARCH}.tar.gz"
        ARCHIVE_EXT="tar.gz"
    fi
    DOWNLOAD_URL="https://github.com/cli/cli/releases/download/v${GH_VERSION}/${ARCHIVE_NAME}"
    CHECKSUM_URL="https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_checksums.txt"
    TMP_ARCHIVE="/tmp/${ARCHIVE_NAME}"
    TMP_CHECKSUMS="/tmp/gh_${GH_VERSION}_checksums.txt"

    echo "[gh] Downloading from ${DOWNLOAD_URL}..."

    curl -fsSL -o "$TMP_ARCHIVE" "$DOWNLOAD_URL"
    curl -fsSL -o "$TMP_CHECKSUMS" "$CHECKSUM_URL"

    EXPECTED_SHA=$(awk -v file="$ARCHIVE_NAME" '$2 == file {print $1}' "$TMP_CHECKSUMS")
    if [ -z "$EXPECTED_SHA" ]; then
        echo "[gh] ERROR: No checksum found for ${ARCHIVE_NAME}"
        exit 1
    fi
    if command -v sha256sum &> /dev/null; then
        ACTUAL_SHA=$(sha256sum "$TMP_ARCHIVE" | awk '{print $1}')
    else
        ACTUAL_SHA=$(shasum -a 256 "$TMP_ARCHIVE" | awk '{print $1}')
    fi
    if [ "$EXPECTED_SHA" != "$ACTUAL_SHA" ]; then
        echo "[gh] ERROR: Checksum mismatch for ${ARCHIVE_NAME}"
        exit 1
    fi

    # Extract based on archive type
    if [ "$ARCHIVE_EXT" = "zip" ]; then
        unzip -q "$TMP_ARCHIVE" -d /tmp
        EXTRACT_DIR="/tmp/gh_${GH_VERSION}_macOS_${ARCH}"
    else
        tar -xzf "$TMP_ARCHIVE" -C /tmp
        EXTRACT_DIR="/tmp/gh_${GH_VERSION}_${OS}_${ARCH}"
    fi

    # Install to ~/.local/bin (works in cloud and local)
    mkdir -p ~/.local/bin
    cp "${EXTRACT_DIR}/bin/gh" ~/.local/bin/gh
    chmod +x ~/.local/bin/gh

    # Clean up
    rm -rf "${EXTRACT_DIR}" "$TMP_ARCHIVE" "$TMP_CHECKSUMS"

    echo "[gh] Installed to ~/.local/bin/gh"
fi

# Verify gh is now in PATH
if ! command -v gh &> /dev/null; then
    echo "[gh] ERROR: gh CLI still not found in PATH after installation"
    echo "[gh] Ensure ~/.local/bin is in your PATH"
    exit 1
fi

# Check authentication status
if [ -n "$GH_TOKEN" ]; then
    # GH_TOKEN is set, verify it works
    if gh auth status &> /dev/null; then
        echo "[gh] Authenticated successfully"
    else
        echo "[gh] WARNING: GH_TOKEN is set but authentication check failed"
        echo "[gh] Token may be invalid or expired"
    fi
else
    echo "[gh] NOTE: GH_TOKEN not set - some operations may require authentication"
    echo "[gh] See: docs/general/agent-setup/github-cli-setup.md"
fi

exit 0
