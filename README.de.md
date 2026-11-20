# Mehrfach-Umbenennen

Viele Dateien auf einmal umbenennen – so einfach wie im Mehrfach-Umbenenn-Tool des Total Commanders.
Für Linux-Desktops mit GTK, eingebunden in den Dateimanager **Nemo** (Linux Mint / Cinnamon).

*English: [README.md](README.md)*

## Warum?

Die üblichen Linux-Umbenenner sind entweder zu schlicht oder sehen aus wie ein Cockpit.
Hier baust du den neuen Namen aus **Bausteinen** zusammen, die du per Klick einfügst – Programmierkenntnisse braucht man nicht:

| Baustein | Bedeutung | Beispiel aus `IMG_0042.jpg` |
|---|---|---|
| `[N]` | alter Name ohne Erweiterung | `IMG_0042` |
| `[N5-8]` | Zeichen 5 bis 8 des alten Namens | `0042` |
| `[N3-]` / `[N-4]` | ab Zeichen 3 / die letzten 4 Zeichen | `G_0042` / `0042` |
| `[E]` | Erweiterung | `jpg` |
| `[C]` | laufender Zähler (Start, Schritt, Stellen einstellbar) | `001` |
| `[YMD]` | Änderungsdatum | `2026-10-03` |
| `[Y]` `[M]` `[D]` | Jahr, Monat, Tag | `2026` `10` `03` |
| `[hms]` | Änderungszeit | `14-05-09` |
| `[P]` | Name des Ordners | `Urlaub` |

**Beispiel:** Maske `2026-10 Foto [C]`, Zähler mit 3 Stellen → `2026-10 Foto 001.jpg`, `2026-10 Foto 002.jpg`, …

Außerdem:

- **Live-Vorschau** aller neuen Namen. Konflikte (doppelte oder schon vorhandene Namen) werden rot markiert – dann wird nichts umbenannt.
- **Teil per Maus auswählen:** Der Knopf „[N#-#] Teil“ zeigt den Namen der ersten Datei, du markierst einfach den Teil, den du behalten willst.
- **Suchen & Ersetzen**, optional nur einmal, mit Erweiterung oder als regulärer Ausdruck.
- **Groß-/Kleinschreibung** ändern.
- **Reihenfolge** (bestimmt den Zähler): nach Name oder Datum sortieren oder Zeilen mit der Maus verschieben.
- **Verlauf:** zuletzt verwendete Masken im Pulldown.
- **Rückgängig** – auch nach einem Neustart.
- **Sicher:** Umbenannt wird zweistufig über temporäre Namen, Tausch (A↔B) klappt, bei einem Fehler wird alles zurückgerollt.
- **Sprachen:** Deutsch, Englisch, Französisch, Spanisch, Italienisch, Niederländisch, Polnisch, Portugiesisch – automatisch nach Systemsprache.

Tastatur: `Strg+Enter` umbenennen, `F1` Hilfe, `Esc` schließen.

## Installation

Benötigt Python 3 und GTK 3 (auf Linux Mint vorinstalliert, sonst `sudo apt install python3-gi gir1.2-gtk-3.0`).

```sh
git clone <repo-url> mehrfach-umbenennen
cd mehrfach-umbenennen
./install.sh
```

Das Installationsskript installiert nur für deinen Benutzer (nach `~/.local`), braucht keine Root-Rechte und **bindet das Tool automatisch in Nemo ein**:

1. **F2 bei mehreren markierten Dateien** öffnet Mehrfach-Umbenennen (Nemo-Einstellung `bulk-rename-tool`; der vorherige Wert wird gemerkt).
2. Im **Rechtsklick-Menü** erscheint „Mehrfach umbenennen …“.
3. Ein **Startmenü-Eintrag** wird angelegt.

Falls der Rechtsklick-Eintrag nicht sofort erscheint: Nemo einmal neu starten mit `nemo -q`.

### Deinstallieren

```sh
./uninstall.sh
```

Stellt auch Nemos vorheriges Umbenenn-Tool wieder her. Deine Einstellungen in `~/.config/mehrfach-umbenennen` bleiben erhalten.

### Manuell in Nemo einbinden (optional)

Das erledigt `install.sh` für dich. Wer es von Hand machen oder das Tool von einem anderen Ort aus nutzen will:

```sh
# F2 bei mehreren markierten Dateien
gsettings set org.nemo.preferences bulk-rename-tool "b'/pfad/zu/mehrfach-umbenennen'"

# zurück zum vorherigen Tool
gsettings reset org.nemo.preferences bulk-rename-tool
```

Für den Rechtsklick-Eintrag `nemo/mehrfach-umbenennen.nemo_action` nach `~/.local/share/nemo/actions/` kopieren und `@LAUNCHER@` durch den Pfad zum Programm ersetzen.

### Ohne Installation ausprobieren

```sh
python3 -m mehrfach_umbenennen DATEI …
```

## Sprachen

Die Sprache richtet sich nach der Systemsprache des Desktops (`LANGUAGE`, `LC_ALL`, `LC_MESSAGES`, `LANG`). Gibt es keine Übersetzung, wird britisches Englisch verwendet.
Andere Sprache testen: `MEHRFACH_UMBENENNEN_LANG=fr python3 -m mehrfach_umbenennen DATEI …`

Die ersten Übersetzungen sind maschinell unterstützt entstanden. **Korrekturen von Muttersprachlern sind sehr willkommen.**

### Übersetzung ergänzen oder verbessern

Die Texte liegen in normalen gettext-Dateien – jeder `.po`-Editor (z. B. Poedit) funktioniert:

1. `mehrfach_umbenennen/locale/messages.pot` nach `mehrfach_umbenennen/locale/<code>.po` kopieren (z. B. `sv.po`) und übersetzen.
2. Den Hilfetext `mehrfach_umbenennen/help/en.txt` nach `help/<code>.txt` übersetzen.
3. In `nemo/*.nemo_action` und `desktop/*.desktop` Zeilen `Name[<code>]` / `Comment[<code>]` ergänzen.
4. Tests laufen lassen – sie prüfen, dass jeder Text übersetzt ist und Platzhalter wie `{n}` erhalten bleiben.

Kompilieren ist nicht nötig, das Programm liest die `.po`-Dateien direkt.

## Entwicklung

Die Umbenenn-Logik steckt ohne GUI in `mehrfach_umbenennen/engine.py`, das Fenster in `app.py`, die Übersetzungen in `i18n.py`.

```sh
python3 -m unittest discover -s tests -v
tools/update-translations.sh   # nach Textänderungen im Code
```

Ideen und Fehlerberichte sind willkommen.

## Lizenz

MIT – siehe [LICENSE](LICENSE).
