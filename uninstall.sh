#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Removes Multi-Rename and restores Nemo's previous bulk-rename tool.
set -eu

DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
PREV="$DATA/linux-speed-rename/vorheriges-nemo-tool"

if [ -f "$PREV" ]; then
    gsettings set org.nemo.preferences bulk-rename-tool "$(cat "$PREV")" || true
elif gsettings list-keys org.nemo.preferences 2>/dev/null | grep -qx bulk-rename-tool; then
    gsettings reset org.nemo.preferences bulk-rename-tool || true
fi

rm -f "$HOME/.local/bin/linux-speed-rename" \
      "$DATA/applications/linux-speed-rename.desktop" \
      "$DATA/nemo/actions/linux-speed-rename.nemo_action"
rm -rf "$DATA/linux-speed-rename/lib" "$PREV"
echo "Removed. Settings in ~/.config/linux-speed-rename and the undo journal are kept."
