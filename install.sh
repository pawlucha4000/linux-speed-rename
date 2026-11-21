#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Installs Multi-Rename (Mehrfach-Umbenennen) for the current user (no root needed)
# and makes it Nemo's bulk-rename tool (F2 with several files selected).
set -eu

SRC="$(cd "$(dirname "$0")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
LIB="$DATA/mehrfach-umbenennen/lib"
BIN="$HOME/.local/bin"
LAUNCHER="$BIN/mehrfach-umbenennen"

python3 -c "import gi; gi.require_version('Gtk', '3.0')" 2>/dev/null || {
    echo "Missing: python3-gi and GTK 3. On Ubuntu/Mint: sudo apt install python3-gi gir1.2-gtk-3.0" >&2
    exit 1
}

mkdir -p "$LIB" "$BIN" "$DATA/applications" "$DATA/nemo/actions"
rm -rf "$LIB/mehrfach_umbenennen"
cp -r "$SRC/mehrfach_umbenennen" "$LIB/"
rm -rf "$LIB/mehrfach_umbenennen/__pycache__"

cat > "$LAUNCHER" <<EOF
#!/bin/sh
PYTHONPATH="$LIB\${PYTHONPATH:+:\$PYTHONPATH}" exec python3 -m mehrfach_umbenennen "\$@"
EOF
chmod +x "$LAUNCHER"

sed "s|@LAUNCHER@|$LAUNCHER|g" "$SRC/desktop/mehrfach-umbenennen.desktop" > "$DATA/applications/mehrfach-umbenennen.desktop"
sed "s|@LAUNCHER@|$LAUNCHER|g" "$SRC/nemo/mehrfach-umbenennen.nemo_action" > "$DATA/nemo/actions/mehrfach-umbenennen.nemo_action"

# Point Nemo's F2 at this tool (remember the previous value so uninstall.sh can restore it)
if gsettings list-keys org.nemo.preferences 2>/dev/null | grep -qx bulk-rename-tool; then
    PREV="$DATA/mehrfach-umbenennen/vorheriges-nemo-tool"
    CUR="$(gsettings get org.nemo.preferences bulk-rename-tool)"
    case "$CUR" in *mehrfach-umbenennen*) ;; *) printf '%s\n' "$CUR" > "$PREV" ;; esac
    gsettings set org.nemo.preferences bulk-rename-tool "b'$LAUNCHER'"
    echo "Nemo: F2 with several files selected now opens Multi-Rename."
fi

echo "Installed. In Nemo: right-click → \"Multi-rename …\" or press F2 with several files selected."
echo "If the menu entry is missing, restart Nemo once: nemo -q"
