#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Installs Linux Speed Rename for the current user (no root needed)
# and makes it Nemo's bulk-rename tool (F2 with several files selected).
set -eu

SRC="$(cd "$(dirname "$0")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
LIB="$DATA/linux-speed-rename/lib"
CFG="${XDG_CONFIG_HOME:-$HOME/.config}"
OLD_DATA="$DATA/mehrfach-umbenennen"
OLD_CFG="$CFG/mehrfach-umbenennen"
NEW_DATA="$DATA/linux-speed-rename"
NEW_CFG="$CFG/linux-speed-rename"
BIN="$HOME/.local/bin"
LAUNCHER="$BIN/linux-speed-rename"

python3 -c "import gi; gi.require_version('Gtk', '3.0')" 2>/dev/null || {
    echo "Missing: python3-gi and GTK 3. On Ubuntu/Mint: sudo apt install python3-gi gir1.2-gtk-3.0" >&2
    exit 1
}

mkdir -p "$LIB" "$BIN" "$DATA/applications" "$DATA/nemo/actions"
mkdir -p "$NEW_CFG" "$NEW_DATA"
copy_old() { [ -f "$1" ] && [ ! -f "$2" ] && cp "$1" "$2" || true; }
copy_old "$OLD_CFG/einstellungen.json" "$NEW_CFG/einstellungen.json"
copy_old "$OLD_DATA/rueckgaengig.json" "$NEW_DATA/rueckgaengig.json"
copy_old "$OLD_DATA/vorheriges-nemo-tool" "$NEW_DATA/vorheriges-nemo-tool"
# alte Programmdateien der Version „Multi-Rename“ entfernen (Nutzerdaten bleiben)
rm -rf "$OLD_DATA/lib"
rm -f "$BIN/mehrfach-umbenennen" "$DATA/applications/mehrfach-umbenennen.desktop" "$DATA/nemo/actions/mehrfach-umbenennen.nemo_action"
rm -rf "$LIB/linux_speed_rename"
cp -r "$SRC/linux_speed_rename" "$LIB/"
rm -rf "$LIB/linux_speed_rename/__pycache__"

cat > "$LAUNCHER" <<EOF
#!/bin/sh
PYTHONPATH="$LIB\${PYTHONPATH:+:\$PYTHONPATH}" exec python3 -m linux_speed_rename "\$@"
EOF
chmod +x "$LAUNCHER"

sed "s|@LAUNCHER@|$LAUNCHER|g" "$SRC/desktop/linux-speed-rename.desktop" > "$DATA/applications/linux-speed-rename.desktop"
sed "s|@LAUNCHER@|$LAUNCHER|g" "$SRC/nemo/linux-speed-rename.nemo_action" > "$DATA/nemo/actions/linux-speed-rename.nemo_action"

# Point Nemo's F2 at this tool (remember the previous value so uninstall.sh can restore it)
if gsettings list-keys org.nemo.preferences 2>/dev/null | grep -qx bulk-rename-tool; then
    PREV="$NEW_DATA/vorheriges-nemo-tool"
    CUR="$(gsettings get org.nemo.preferences bulk-rename-tool)"
    case "$CUR" in *linux-speed-rename*|*mehrfach-umbenennen*) ;; *) printf '%s\n' "$CUR" > "$PREV" ;; esac
    gsettings set org.nemo.preferences bulk-rename-tool "b'$LAUNCHER'"
    echo "Nemo: F2 with several files selected now opens Linux Speed Rename."
fi

echo "Installed. In Nemo: right-click → \"Linux Speed Rename …\" or press F2 with several files selected."
echo "If the menu entry is missing, restart Nemo once: nemo -q"
