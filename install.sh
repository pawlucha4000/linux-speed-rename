#!/bin/sh
# Installiert Mehrfach-Umbenennen für den aktuellen Benutzer (keine Root-Rechte nötig)
# und macht es zum Umbenenn-Tool von Nemo (F2 bei mehreren markierten Dateien).
set -eu

SRC="$(cd "$(dirname "$0")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
LIB="$DATA/mehrfach-umbenennen/lib"
BIN="$HOME/.local/bin"
LAUNCHER="$BIN/mehrfach-umbenennen"

python3 -c "import gi; gi.require_version('Gtk', '3.0')" 2>/dev/null || {
    echo "Fehlt: python3-gi und GTK 3. Unter Ubuntu/Mint: sudo apt install python3-gi gir1.2-gtk-3.0" >&2
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

# F2 in Nemo auf dieses Tool umstellen (vorherigen Wert merken, damit uninstall.sh ihn zurücksetzt)
if gsettings list-keys org.nemo.preferences 2>/dev/null | grep -qx bulk-rename-tool; then
    PREV="$DATA/mehrfach-umbenennen/vorheriges-nemo-tool"
    CUR="$(gsettings get org.nemo.preferences bulk-rename-tool)"
    case "$CUR" in *mehrfach-umbenennen*) ;; *) printf '%s\n' "$CUR" > "$PREV" ;; esac
    gsettings set org.nemo.preferences bulk-rename-tool "b'$LAUNCHER'"
    echo "Nemo: F2 bei mehreren Dateien öffnet jetzt Mehrfach-Umbenennen."
fi

echo "Installiert. Rechtsklick in Nemo → „Mehrfach umbenennen …“ oder F2 bei mehreren markierten Dateien."
echo "Falls der Menüeintrag fehlt: Nemo einmal neu starten (nemo -q)."
