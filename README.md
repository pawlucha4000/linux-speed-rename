# Mehrfach-Umbenennen

Viele Dateien auf einmal umbenennen – so einfach wie im Mehrfach-Umbenenn-Tool des Total Commanders.
Für Linux-Desktops mit GTK, eingebunden in den Dateimanager **Nemo** (Linux Mint / Cinnamon).

*English summary: a Total-Commander-style multi-rename tool for Linux (GTK 3, Python). It plugs into Nemo as its bulk-rename tool (F2 with several files selected) and as a context-menu action. The UI is currently German.*

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

- **Live-Vorschau** aller neuen Namen, Konflikte (doppelte oder schon vorhandene Namen) werden rot markiert – dann wird nichts umbenannt.
- **Teil auswählen** per Maus: Der Knopf „[N#-#] Teil“ zeigt den Namen der ersten Datei, du markierst einfach den Teil, den du behalten willst.
- **Suchen & Ersetzen**, optional nur einmal, mit Erweiterung oder als regulärer Ausdruck.
- **Groß-/Kleinschreibung** ändern.
- **Reihenfolge** (bestimmt den Zähler): nach Name oder Datum sortieren oder Zeilen mit der Maus verschieben.
- **Verlauf**: zuletzt verwendete Masken im Pulldown.
- **Rückgängig** – auch nach einem Neustart.
- Sicher: Umbenannt wird zweistufig über temporäre Namen, Tausch (A↔B) klappt, bei einem Fehler wird alles zurückgerollt.

Tastatur: `Strg+Enter` umbenennen, `F1` Hilfe, `Esc` schließen.

## Installation

Benötigt Python 3 und GTK 3 (auf Linux Mint vorinstalliert, sonst `sudo apt install python3-gi gir1.2-gtk-3.0`).

```sh
git clone <repo-url> mehrfach-umbenennen
cd mehrfach-umbenennen
./install.sh
```

Das installiert nur für deinen Benutzer (nach `~/.local`), ohne Root-Rechte, und

- stellt Nemo so ein, dass **F2 bei mehreren markierten Dateien** dieses Tool öffnet (`org.nemo.preferences bulk-rename-tool`),
- fügt im Rechtsklick-Menü von Nemo **„Mehrfach umbenennen …“** hinzu,
- legt einen Startmenü-Eintrag an.

Entfernen: `./uninstall.sh` – stellt auch Nemos vorheriges Umbenenn-Tool wieder her.

Ohne Installation ausprobieren: `python3 -m mehrfach_umbenennen DATEI …`

## Entwicklung

Die Umbenenn-Logik steckt ohne GUI in `mehrfach_umbenennen/engine.py`, die Oberfläche in `app.py`.

```sh
python3 -m unittest discover -s tests -v
```

Ideen und Fehlerberichte sind willkommen.

## Lizenz

MIT – siehe [LICENSE](LICENSE).
