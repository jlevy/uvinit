#!/bin/bash
# Ensure tbd CLI is installed and run tbd prime for Claude Code sessions
# Installed by: tbd setup --auto
# This script runs on SessionStart and PreCompact

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_DIR=$(cd "$SCRIPT_DIR/../.." && pwd)
TBD_VERSION=$(awk -F': *' '/^tbd_version:/ {print $2; exit}' "$PROJECT_DIR/.tbd/config.yml" 2>/dev/null)
TBD_PACKAGE="get-tbd"
if [ -n "$TBD_VERSION" ]; then
    TBD_PACKAGE="get-tbd@${TBD_VERSION}"
fi

# Get npm global bin directory (if npm is available)
NPM_GLOBAL_BIN=""
if command -v npm &> /dev/null; then
    NPM_PREFIX=$(npm config get prefix 2>/dev/null)
    if [ -n "$NPM_PREFIX" ] && [ -d "$NPM_PREFIX/bin" ]; then
        NPM_GLOBAL_BIN="$NPM_PREFIX/bin"
    fi
fi

# Add common binary locations to PATH (persists for entire script)
# Include npm global bin if found
export PATH="$NPM_GLOBAL_BIN:$HOME/.local/bin:$HOME/bin:/usr/local/bin:$PATH"

# Function to ensure tbd is available
ensure_tbd() {
    # Check if tbd is already installed
    if command -v tbd &> /dev/null; then
        return 0
    fi

    echo "[tbd] CLI not found, installing..."

    # Try npm first (most common for Node.js tools)
    if command -v npm &> /dev/null; then
        echo "[tbd] Installing ${TBD_PACKAGE} via npm..."
        npm install -g "$TBD_PACKAGE" 2>/dev/null || {
            # If global install fails (permissions), try local install
            echo "[tbd] Global npm install failed, trying user install..."
            mkdir -p ~/.local/bin
            npm install --prefix ~/.local "$TBD_PACKAGE"
            # Create symlink if needed
            if [ -f ~/.local/node_modules/.bin/tbd ]; then
                ln -sf ~/.local/node_modules/.bin/tbd ~/.local/bin/tbd
            fi
        }
    elif command -v pnpm &> /dev/null; then
        echo "[tbd] Installing ${TBD_PACKAGE} via pnpm..."
        pnpm add -g "$TBD_PACKAGE"
    elif command -v yarn &> /dev/null; then
        echo "[tbd] Installing ${TBD_PACKAGE} via yarn..."
        yarn global add "$TBD_PACKAGE"
    else
        echo "[tbd] ERROR: No package manager found (npm, pnpm, or yarn required)"
        echo "[tbd] Please install Node.js and npm, then run: npm install -g ${TBD_PACKAGE}"
        return 1
    fi

    # Verify installation
    if command -v tbd &> /dev/null; then
        echo "[tbd] Successfully installed to $(which tbd)"
        return 0
    else
        echo "[tbd] WARNING: tbd installed but not found in PATH"
        echo "[tbd] Checking common locations..."
        # Try to find and add to path (include npm global bin)
        for dir in "$NPM_GLOBAL_BIN" ~/.local/bin ~/.local/node_modules/.bin /usr/local/bin; do
            if [ -n "$dir" ] && [ -x "$dir/tbd" ]; then
                export PATH="$dir:$PATH"
                echo "[tbd] Found at $dir/tbd"
                return 0
            fi
        done
        echo "[tbd] Could not locate tbd after installation"
        return 1
    fi
}

# Main
ensure_tbd || exit 1

# Run tbd prime with any passed arguments (e.g., --brief for PreCompact)
tbd prime "$@"
