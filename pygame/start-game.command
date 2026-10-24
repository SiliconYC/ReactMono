#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Double-click in macOS Finder to start the real Pygame game.

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd -P)" || exit 1
cd "$PROJECT_DIR" || exit 1
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

pause_on_error() {
  printf '\nLaunch failed. Press Return to close this window...'
  if [ -t 0 ]; then read -r _; else printf '\n'; fi
}

if [ ! -f assets/manifest.json ]; then
  echo "Game assets are missing: $PROJECT_DIR/assets/manifest.json"
  echo "Import your licensed assets first (see pygame/README.md)."
  pause_on_error
  exit 1
fi

if command -v uv >/dev/null 2>&1; then
  uv run --project "$PROJECT_DIR" --python 3.12 rich4-pygame
elif [ -x .venv/bin/rich4-pygame ]; then
  .venv/bin/rich4-pygame
else
  echo "Neither uv nor an installed Pygame environment was found."
  echo "Install uv, then follow the one-time setup in pygame/README.md."
  pause_on_error
  exit 1
fi

status=$?
if [ "$status" -ne 0 ]; then
  echo "Game exited with error code $status."
  pause_on_error
fi
exit "$status"
