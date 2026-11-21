# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Paul Bittner
"""Umbenenn-Logik ohne GUI: Masken auswerten, Vorschau berechnen, umbenennen, rückgängig machen.

Platzhalter (wie im Total Commander):
  [N]       ganzer alter Dateiname ohne Erweiterung
  [N2-5]    Zeichen 2 bis 5 des alten Namens (ab 1 gezählt)
  [N3]      nur Zeichen 3
  [N3-]     ab Zeichen 3 bis zum Ende
  [N-3]     die letzten 3 Zeichen
  [E], [E1-2] ... dasselbe für die Erweiterung
  [C]       Zähler (Start, Schrittweite, Stellen einstellbar)
  [YMD]     Änderungsdatum als JJJJ-MM-TT
  [Y] [M] [D]  Jahr, Monat, Tag einzeln
  [hms]     Änderungszeit als hh-mm-ss
  [h] [m] [s]  Stunde, Minute, Sekunde einzeln
  [P]       Name des Ordners, in dem die Datei liegt
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import json
import os
import re
import uuid
from dataclasses import dataclass

from .i18n import _

TOKEN_RE = re.compile(
    r"\[(?:"
    r"(?P<part>[NE])(?:(?P<neg>-)(?P<last>\d+)|(?P<a>\d+)(?:(?P<dash>-)(?P<b>\d+)?)?)?"
    r"|(?P<simple>C|YMD|hms|Y|M|D|h|m|s|P)"
    r")\]"
)

CASE_OPTIONS = [_("Unchanged"), _("lowercase"), _("UPPERCASE"), _("First letter capital"), _("Each Word Capitalised")]


@dataclass
class Settings:
    name_mask: str = "[N]"
    ext_mask: str = "[E]"
    search: str = ""
    replace: str = ""
    regex: bool = False
    once: bool = False
    include_ext: bool = False  # Suchen & Ersetzen auch in der Erweiterung
    case: int = 0
    counter_start: int = 1
    counter_step: int = 1
    counter_digits: int = 1


@dataclass
class Entry:
    path: str
    new_name: str = ""
    error: str = ""

    @property
    def directory(self) -> str:
        return os.path.dirname(self.path)

    @property
    def old_name(self) -> str:
        return os.path.basename(self.path)

    @property
    def new_path(self) -> str:
        return os.path.join(self.directory, self.new_name)

    @property
    def changed(self) -> bool:
        return self.new_name != self.old_name


def split_name(filename: str) -> tuple[str, str]:
    """Trennt 'foto.jpg' in ('foto', 'jpg'). Versteckte Dateien wie '.bashrc' haben keine Erweiterung."""
    base, ext = os.path.splitext(filename)
    return base, ext[1:] if ext else ""


def _slice(text: str, m: re.Match) -> str:
    if m.group("neg"):
        n = int(m.group("last"))
        return text[-n:] if n else ""
    if m.group("a") is None:
        return text
    a = max(int(m.group("a")), 1) - 1
    if m.group("dash"):
        b = m.group("b")
        return text[a:int(b)] if b else text[a:]
    return text[a:a + 1]


def expand(mask: str, base: str, ext: str, counter: str, mtime: _dt.datetime, parent: str) -> str:
    def repl(m: re.Match) -> str:
        if m.group("part"):
            return _slice(base if m.group("part") == "N" else ext, m)
        s = m.group("simple")
        return {
            "C": counter,
            "YMD": mtime.strftime("%Y-%m-%d"),
            "Y": mtime.strftime("%Y"),
            "M": mtime.strftime("%m"),
            "D": mtime.strftime("%d"),
            "hms": mtime.strftime("%H-%M-%S"),
            "h": mtime.strftime("%H"),
            "m": mtime.strftime("%M"),
            "s": mtime.strftime("%S"),
            "P": parent,
        }[s]

    return TOKEN_RE.sub(repl, mask)


def _apply_case(text: str, mode: int) -> str:
    if mode == 1:
        return text.lower()
    if mode == 2:
        return text.upper()
    if mode == 3:
        return text[:1].upper() + text[1:].lower()
    if mode == 4:
        return re.sub(r"[^\W_]+", lambda m: m.group(0)[:1].upper() + m.group(0)[1:].lower(), text)
    return text


_GROUP_REF = re.compile(r"\$\$|\$\{(\d+)\}|\$(\d)|\\(\d)|\\\\")


class ReplaceError(ValueError):
    pass


def _regex_replacement(repl: str):
    """Ersetzungstext für reguläre Ausdrücke.

    Wie im Total Commander steht $1 für die erste Klammer, $2 für die zweite usw.
    Auch \\1 und ${10} gehen; $$ ergibt ein Dollarzeichen. Alles andere bleibt wörtlich.
    """

    def build(m: re.Match) -> str:
        def ref(r: re.Match) -> str:
            tok = r.group(0)
            if tok == "$$":
                return "$"
            if tok == "\\\\":
                return "\\"
            n = int(r.group(1) or r.group(2) or r.group(3))
            if n > (m.re.groups or 0):
                raise ReplaceError(_("Group ${n} does not exist in the search pattern").format(n=n))
            return m.group(n) or ""

        return _GROUP_REF.sub(ref, repl)

    return build


def _search_replace(text: str, s: Settings) -> str:
    if not s.search:
        return text
    count = 1 if s.once else 0
    if s.regex:
        return re.sub(s.search, _regex_replacement(s.replace), text, count=count)
    if s.once:
        return text.replace(s.search, s.replace, 1)
    return text.replace(s.search, s.replace)


def _mtime(path: str) -> _dt.datetime:
    try:
        return _dt.datetime.fromtimestamp(os.path.getmtime(path))
    except OSError:
        return _dt.datetime.now()


def compute(paths: list[str], s: Settings) -> list[Entry]:
    """Berechnet die neuen Namen und markiert Konflikte. Ändert nichts auf der Platte."""
    if s.regex and s.search:
        try:
            re.compile(s.search)
        except re.error as exc:
            return [Entry(p, os.path.basename(p), _("Invalid regular expression: {error}").format(error=exc)) for p in paths]

    entries: list[Entry] = []
    for i, path in enumerate(paths):
        old = os.path.basename(path)
        base, ext = split_name(old)
        counter = str(s.counter_start + i * s.counter_step).zfill(max(s.counter_digits, 1))
        mtime = _mtime(path)
        parent = os.path.basename(os.path.dirname(path))
        new_base = expand(s.name_mask, base, ext, counter, mtime, parent)
        new_ext = expand(s.ext_mask, base, ext, counter, mtime, parent)
        try:
            if s.include_ext:
                full = new_base + ("." + new_ext if new_ext else "")
                full = _search_replace(full, s)
            else:
                new_base = _search_replace(new_base, s)
                full = new_base + ("." + new_ext if new_ext else "")
        except ReplaceError as exc:
            entries.append(Entry(path, old, str(exc)))
            continue
        full = _apply_case(full, s.case)
        entries.append(Entry(path, full))

    _check_conflicts(entries)
    return entries


def _check_conflicts(entries: list[Entry]) -> None:
    sources = {os.path.abspath(e.path) for e in entries}
    seen: dict[str, Entry] = {}
    for e in entries:
        name = e.new_name
        if not name.strip():
            e.error = _("Empty name")
        elif "/" in name or "\0" in name:
            e.error = _("Name contains '/'")
        elif name in (".", ".."):
            e.error = _("Invalid name")
        elif len(name.encode()) > 255:
            e.error = _("Name too long")
        target = os.path.abspath(e.new_path)
        key = target
        if key in seen and not e.error:
            e.error = _("Duplicate name")
            if not seen[key].error:
                seen[key].error = _("Duplicate name")
        seen.setdefault(key, e)
        if not e.error and e.changed and os.path.lexists(target) and target not in sources:
            # Auf Laufwerken ohne Groß-/Kleinunterscheidung (FAT, NTFS) ist das Ziel
            # bei reiner Schreibweisen-Änderung dieselbe Datei – das ist erlaubt.
            try:
                same = os.path.samefile(target, e.path)
            except OSError:
                same = False
            if not same:
                e.error = _("File already exists")


def has_errors(entries: list[Entry]) -> bool:
    return any(e.error for e in entries)


def execute(entries: list[Entry]) -> list[tuple[str, str]]:
    """Benennt um (zweistufig über temporäre Namen, damit Tausch und Ketten klappen).

    Gibt die Liste (alt, neu) der tatsächlich umbenannten Dateien zurück.
    """
    if has_errors(entries):
        raise ValueError(_("There are conflicts, please resolve them first."))
    todo = [e for e in entries if e.changed]
    staged: list[tuple[Entry, str]] = []
    done: list[tuple[str, str]] = []
    try:
        for e in todo:
            tmp = os.path.join(e.directory, f".linux-speed-rename-{uuid.uuid4().hex}")
            os.rename(e.path, tmp)
            staged.append((e, tmp))
        while staged:
            e, tmp = staged[0]
            if os.path.lexists(e.new_path):
                raise FileExistsError(_("Target already exists: {path}").format(path=e.new_path))
            os.rename(tmp, e.new_path)
            staged.pop(0)
            done.append((e.path, e.new_path))
    except Exception:
        # Zurückrollen: was schon fertig ist, zurück; was noch temporär liegt, zurück.
        for old, new in reversed(done):
            try:
                os.rename(new, old)
            except OSError:
                pass
        for e, tmp in staged:
            try:
                os.rename(tmp, e.path)
            except OSError:
                pass
        raise
    return done


# ---------- Rückgängig-Protokoll ----------

def journal_path() -> str:
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, "linux-speed-rename", "rueckgaengig.json")


def save_journal(done: list[tuple[str, str]]) -> None:
    if not done:
        return
    path = journal_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {"zeit": _dt.datetime.now().isoformat(timespec="seconds"), "umbenannt": done}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def load_journal() -> list[tuple[str, str]]:
    try:
        with open(journal_path(), encoding="utf-8") as f:
            return [tuple(p) for p in json.load(f)["umbenannt"]]
    except (OSError, ValueError, KeyError):
        return []


def undo_last() -> list[tuple[str, str]]:
    """Macht die letzte Umbenennung rückgängig. Gibt (neu, alt) der zurückbenannten Dateien zurück."""
    done = load_journal()
    if not done:
        return []
    entries = []
    for old, new in done:
        if os.path.lexists(new):
            e = Entry(new, os.path.basename(old))
            if os.path.dirname(old) != os.path.dirname(new):
                continue
            entries.append(e)
    _check_conflicts(entries)
    reverted = execute(entries)
    try:
        os.remove(journal_path())
    except OSError:
        pass
    return reverted


# ---------- Gespeicherte Einstellungen / zuletzt verwendete Masken ----------

def _config_path() -> str:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "linux-speed-rename", "einstellungen.json")


def load_config() -> dict:
    try:
        with open(_config_path(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_config(cfg: dict) -> None:
    path = _config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=1)


def settings_to_dict(s: Settings) -> dict:
    return dataclasses.asdict(s)


def settings_from_dict(d: dict) -> Settings:
    """Liest gespeicherte Einstellungen; unbekannte oder kaputte Werte werden ignoriert."""
    s = Settings()
    for f in dataclasses.fields(Settings):
        if f.name in d and isinstance(d[f.name], type(getattr(s, f.name))):
            setattr(s, f.name, d[f.name])
    return s


def remember(cfg: dict, key: str, value: str, limit: int = 15) -> None:
    if not value:
        return
    items = [v for v in cfg.get(key, []) if v != value]
    cfg[key] = [value] + items[:limit - 1]
