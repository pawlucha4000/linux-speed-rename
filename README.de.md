# Linux Speed Rename

Ein übersichtliches, intuitiv zu bedienendes Tool zum Umbenennen von einigen wenigen oder sehr, sehr vielen Dateien, das sich nahtlos in die Linux-Umgebung einfügt.
Konzipiert als bedienungsfreundliche Integration für den Linux-Dateimanager **Nemo** (Linux Mint / Cinnamon) – nach dem Vorbild des Mehrfach-Umbenenn-Tools im Total Commander.

Version 1.0.0 vom 2026-11-21 · Programmierung: Paul Bittner · Lizenz: GNU GPL v3 oder neuer

*English: [README.md](README.md)*

## So benutzt du das Tool

Nach der Installation den Dateimanager Nemo öffnen, die Dateien markieren, die umbenannt werden sollen, und **F2** drücken.

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
- **Einstellungen speichern (F2):** alle Felder unter einem Namen ablegen und später wieder laden – siehe unten.
- **Reguläre Ausdrücke** mit `$1`, `$2` … wie im Total Commander – siehe die einfachen Beispiele unten.
- **Rückgängig** – auch nach einem Neustart.
- **Sicher:** Umbenannt wird zweistufig über temporäre Namen, Tausch (A↔B) klappt, bei einem Fehler wird alles zurückgerollt.
- **Sprachen:** Deutsch, Englisch, Französisch, Spanisch, Italienisch, Niederländisch, Polnisch, Portugiesisch – automatisch nach Systemsprache.

Tastatur: `Strg+Enter` umbenennen, `F1` Hilfe, `F2` gespeicherte Einstellungen, `Esc` schließen. Der Knopf **Über** zeigt Version, Programmierer und Lizenz (auf der Kommandozeile: `--version`).

## Einstellungen speichern (F2)

Komplizierte Einstellungen musst du nicht jedes Mal neu eintippen. Das Pulldown **„F2 Einstellungen laden/speichern“** (unter dem Zähler) speichert *alle* Felder – Masken, Suchen & Ersetzen, Optionen, Zähler – unter einem Namen deiner Wahl:

- **Einstellungen speichern …** – die aktuellen Felder ablegen (neuen Namen eingeben oder einen vorhandenen wählen, um ihn zu überschreiben).
- Einen gespeicherten Namen wählen – alle Felder werden wieder ausgefüllt.
- **Eintrag löschen …** – die gerade geladenen Einstellungen entfernen.
- **&lt;Standard&gt;** – zurück zu den einfachen Startwerten.

Mit **F2** im Fenster öffnest du die Liste. Gespeichert wird in `~/.config/mehrfach-umbenennen/` (siehe unten).

## Reguläre Ausdrücke – einfache Beispiele

Reguläre Ausdrücke *braucht* man nie, aber sie helfen, wenn Namen einem festen Muster folgen und du Teile davon umstellen willst.
Setze den Haken bei **„Regulärer Ausdruck“** und verwende im Feld **Suchen nach** diese Bausteine:

| Schreibweise | Bedeutung |
|---|---|
| `\S+` | ein Wort ohne Leerzeichen (z. B. `K733142`) |
| `\d` / `\d+` | eine Ziffer / eine oder mehrere Ziffern |
| `.*` | beliebiger Text (auch leer) |
| `^` / `$` | Anfang / Ende des Namens |
| `\.` `\(` `\)` | ein echter Punkt, eine echte Klammer (sonst haben sie eine Sonderbedeutung) |
| `( … )` | diesen Teil **merken** … |
| `$1`, `$2` … | … und im Feld **Ersetzen durch** wieder einsetzen (1. Klammer, 2. Klammer …) |

**Beispiele** (die Erweiterung, z. B. `.jpg`, bleibt unberührt, außer „auch in Erweiterung“ ist angehakt):

| Aufgabe | Suchen nach | Ersetzen durch | Vorher → nachher |
|---|---|---|---|
| Zeichnungs-Export aufräumen | `^(\S+) - (\S+) - (\S+) - (.*)$` | `$1-$2.$3.$4` | `K733142 - EN - 1 - - Zeichnung Objekt` → `K733142-EN.1.- Zeichnung Objekt` |
| Datum umdrehen | `^(\d\d)\.(\d\d)\.(\d{4})` | `$3-$2-$1` | `03.10.2026 Rechnung` → `2026-10-03 Rechnung` |
| Zwei Wörter tauschen | `^(\S+) (\S+)$` | `$2 $1` | `Müller Hans` → `Hans Müller` |
| Klammer samt Inhalt entfernen | ` ?\(.*?\)` | *(leer)* | `Foto (Kopie)` → `Foto` |
| Nummer am Anfang entfernen | `^\d+\s*-\s*` | *(leer)* | `07 - Lied` → `Lied` |
| Unterstriche und mehrfache Leerzeichen → ein Leerzeichen | `[ _]+` | ` ` *(ein Leerzeichen)* | `Mein__Urlaub   2026` → `Mein Urlaub 2026` |

So liest sich das erste Beispiel: `^(\S+) - (\S+) - (\S+) - (.*)$` heißt *„am Anfang ein Wort (1), dann ` - `, ein Wort (2), ` - `, ein Wort (3), ` - ` und der Rest bis zum Ende (4)“*. Die Ersetzung `$1-$2.$3.$4` klebt die vier gemerkten Teile mit `-`, `.` und `.` wieder zusammen.

Tipp: Beobachte beim Tippen die **Vorschau** – sie zeigt das Ergebnis sofort. Ein Muster, das du öfter brauchst, speicherst du mit **F2 → Einstellungen speichern …**.

## Installation

Benötigt Python 3 und GTK 3 (auf Linux Mint vorinstalliert, sonst `sudo apt install python3-gi gir1.2-gtk-3.0`).

```sh
git clone <repo-url> mehrfach-umbenennen
cd mehrfach-umbenennen
./install.sh
```

Das Installationsskript installiert nur für deinen Benutzer (nach `~/.local`), braucht keine Root-Rechte und **bindet das Tool automatisch in Nemo ein**:

1. **F2 bei mehreren markierten Dateien** öffnet Linux Speed Rename (Nemo-Einstellung `bulk-rename-tool`; der vorherige Wert wird gemerkt).
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

Copyright © 2026 Paul Bittner

Dieses Programm ist freie Software: Du kannst es unter den Bedingungen der GNU General Public License, wie von der Free Software Foundation veröffentlicht, weitergeben und/oder verändern – entweder gemäß Version 3 der Lizenz oder (nach deiner Wahl) jeder späteren Version. Es wird in der Hoffnung verbreitet, dass es nützlich ist, aber OHNE JEDE GEWÄHRLEISTUNG. Den vollständigen (englischen) Lizenztext findest du in [LICENSE](LICENSE).
