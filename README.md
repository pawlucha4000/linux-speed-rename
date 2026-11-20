# Multi-Rename (Mehrfach-Umbenennen)

Rename many files at once – as easily as with the multi-rename tool of Total Commander.
For GTK desktops on Linux, built into the **Nemo** file manager (Linux Mint / Cinnamon).

*Deutsch: [README.de.md](README.de.md)*

## Why?

The usual Linux bulk renamers are either too basic or look like an aircraft cockpit.
Here you build the new name from **building blocks** that you insert with a click – no programming knowledge needed:

| Block | Meaning | Example for `IMG_0042.jpg` |
|---|---|---|
| `[N]` | old name without extension | `IMG_0042` |
| `[N5-8]` | characters 5 to 8 of the old name | `0042` |
| `[N3-]` / `[N-4]` | from character 3 / the last 4 characters | `G_0042` / `0042` |
| `[E]` | extension | `jpg` |
| `[C]` | running counter (start, step, digits adjustable) | `001` |
| `[YMD]` | modification date | `2026-10-03` |
| `[Y]` `[M]` `[D]` | year, month, day | `2026` `10` `03` |
| `[hms]` | modification time | `14-05-09` |
| `[P]` | name of the folder | `Holiday` |

**Example:** mask `2026-10 Photo [C]`, counter with 3 digits → `2026-10 Photo 001.jpg`, `2026-10 Photo 002.jpg`, …

Also:

- **Live preview** of all new names. Conflicts (duplicate or already existing names) are shown in red – then nothing is renamed.
- **Select a part with the mouse:** the “[N#-#] Part” button shows the first file name, you simply select the part you want to keep.
- **Search & Replace**, optionally only once, including the extension, or as a regular expression.
- **Change case** (lower, UPPER, Title …).
- **Order** (sets the counter): sort by name or date, or drag rows with the mouse.
- **History:** recently used masks in the drop-down.
- **Undo** – even after restarting the program.
- **Safe:** renaming happens in two steps via temporary names, so swapping names (A↔B) works, and on any error everything is rolled back.
- **Languages:** English, German, French, Spanish, Italian, Dutch, Polish, Portuguese – picked automatically from the system language.

Keyboard: `Ctrl+Enter` rename, `F1` help, `Esc` close.

## Installation

Requires Python 3 and GTK 3 (pre-installed on Linux Mint; otherwise `sudo apt install python3-gi gir1.2-gtk-3.0`).

```sh
git clone <repo-url> mehrfach-umbenennen
cd mehrfach-umbenennen
./install.sh
```

The installer works for your user only (into `~/.local`), needs no root rights, and **integrates the tool into Nemo automatically**:

1. **F2 with several files selected** opens Multi-Rename (Nemo setting `bulk-rename-tool`; the previous value is saved).
2. **Right-click menu** gets the entry “Multi-rename …”.
3. A **start menu entry** is created.

If the right-click entry does not show up straight away, restart Nemo once: `nemo -q`.

### Uninstall

```sh
./uninstall.sh
```

This also restores Nemo's previous rename tool. Your settings in `~/.config/mehrfach-umbenennen` stay.

### Manual integration into Nemo (optional)

`install.sh` does this for you. If you want to do it by hand, or use the tool from another location:

```sh
# F2 with several files selected
gsettings set org.nemo.preferences bulk-rename-tool "b'/path/to/mehrfach-umbenennen'"

# back to the previous tool (e.g. on Linux Mint 22)
gsettings reset org.nemo.preferences bulk-rename-tool
```

For the right-click entry, copy `nemo/mehrfach-umbenennen.nemo_action` to `~/.local/share/nemo/actions/` and replace `@LAUNCHER@` with the path to the program.

### Try without installing

```sh
python3 -m mehrfach_umbenennen FILE …
```

## Languages

The language follows the desktop's system language (`LANGUAGE`, `LC_ALL`, `LC_MESSAGES`, `LANG`). If there is no translation, British English is used.
To test another language: `MEHRFACH_UMBENENNEN_LANG=fr python3 -m mehrfach_umbenennen FILE …`

The initial translations were machine-assisted. **Corrections by native speakers are very welcome.**

### Adding or improving a translation

Texts are in standard gettext files – any `.po` editor (e.g. Poedit) works:

1. Copy `mehrfach_umbenennen/locale/messages.pot` to `mehrfach_umbenennen/locale/<code>.po` (e.g. `sv.po`) and translate it.
2. Translate the help text `mehrfach_umbenennen/help/en.txt` into `help/<code>.txt`.
3. Add `Name[<code>]` / `Comment[<code>]` lines to `nemo/*.nemo_action` and `desktop/*.desktop`.
4. Run the tests – they check that every text is translated and placeholders like `{n}` are kept.

No compilation step is needed; the program reads the `.po` files directly.

## Development

The renaming logic lives without any GUI in `mehrfach_umbenennen/engine.py`, the window in `app.py`, translations in `i18n.py`.

```sh
python3 -m unittest discover -s tests -v
tools/update-translations.sh   # after changing texts in the code
```

Ideas and bug reports are welcome.

## Licence

MIT – see [LICENSE](LICENSE).
