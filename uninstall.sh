#!/bin/sh
# Entfernt Mehrfach-Umbenennen und stellt Nemos vorheriges Umbenenn-Tool wieder her.
set -eu

DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
PREV="$DATA/mehrfach-umbenennen/vorheriges-nemo-tool"

if [ -f "$PREV" ]; then
    gsettings set org.nemo.preferences bulk-rename-tool "$(cat "$PREV")" || true
elif gsettings list-keys org.nemo.preferences 2>/dev/null | grep -qx bulk-rename-tool; then
    gsettings reset org.nemo.preferences bulk-rename-tool || true
fi

rm -f "$HOME/.local/bin/mehrfach-umbenennen" \
      "$DATA/applications/mehrfach-umbenennen.desktop" \
      "$DATA/nemo/actions/mehrfach-umbenennen.nemo_action"
rm -rf "$DATA/mehrfach-umbenennen/lib" "$PREV"
echo "Entfernt. Einstellungen in ~/.config/mehrfach-umbenennen und das Rückgängig-Protokoll bleiben erhalten."
