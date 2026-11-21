# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Paul Bittner
"""Übersetzungen / translations.

The source language of all texts is British English. Translations live in standard
gettext ``.po`` files in ``locale/<code>.po`` and are read directly at start-up,
so no compilation step (msgfmt) is needed. The language follows the desktop's
system language (LANGUAGE, LC_ALL, LC_MESSAGES, LANG); if there is no
translation for it, British English is used.

Set ``LINUX_SPEED_RENAME_LANG=fr`` to force a language for testing.
"""

from __future__ import annotations

import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
LOCALE_DIR = os.path.join(_HERE, "locale")
HELP_DIR = os.path.join(_HERE, "help")

_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1]
    return re.sub(r"\\(.)", lambda m: _ESCAPES.get(m.group(1), m.group(0)), s)


def load_po(path: str) -> dict[str, str]:
    """Minimal .po reader: msgid/msgstr incl. multi-line strings; skips fuzzy and empty entries."""
    catalog: dict[str, str] = {}
    msgid = msgstr = None
    cur = None
    fuzzy = next_fuzzy = False

    def add():
        if msgid and msgstr and not fuzzy:
            catalog[msgid] = msgstr

    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("#"):
                if line.startswith("#,") and "fuzzy" in line:
                    next_fuzzy = True
                continue
            if line.startswith("msgid "):
                if msgid is not None:
                    add()
                msgid, msgstr, cur = _unquote(line[6:]), None, "id"
                fuzzy, next_fuzzy = next_fuzzy, False
            elif line.startswith("msgstr "):
                msgstr, cur = _unquote(line[7:]), "str"
            elif line.startswith('"'):
                if cur == "id":
                    msgid += _unquote(line)
                elif cur == "str" and msgstr is not None:
                    msgstr += _unquote(line)
    if msgid is not None:
        add()
    return catalog


def available_languages() -> list[str]:
    try:
        codes = [f[:-3] for f in os.listdir(LOCALE_DIR) if f.endswith(".po")]
    except OSError:
        codes = []
    return sorted(["en"] + codes)


def wanted_languages(env: dict | None = None) -> list[str]:
    """Languages the user wants, most preferred first, e.g. ['de_AT', 'de']."""
    env = os.environ if env is None else env
    raw: list[str] = []
    forced = env.get("LINUX_SPEED_RENAME_LANG")
    if forced:
        raw.append(forced)
    if env.get("LANGUAGE"):
        raw += env["LANGUAGE"].split(":")
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        if env.get(var):
            raw.append(env[var])
            break
    out: list[str] = []
    for item in raw:
        code = item.split(".")[0].split("@")[0]
        if not code or code in ("C", "POSIX"):
            continue
        for cand in (code, code.split("_")[0]):
            if cand not in out:
                out.append(cand)
    return out


def pick_language(env: dict | None = None) -> str:
    have = set(available_languages())
    for code in wanted_languages(env):
        if code in have:
            return code
    return "en"


LANG = pick_language()
_catalog: dict[str, str] = {}
if LANG != "en":
    try:
        _catalog = load_po(os.path.join(LOCALE_DIR, LANG + ".po"))
    except OSError:
        _catalog = {}


def _(text: str) -> str:
    return _catalog.get(text, text)


def help_text() -> str:
    for code in (LANG, "en"):
        try:
            with open(os.path.join(HELP_DIR, code + ".txt"), encoding="utf-8") as f:
                return f.read().strip()
        except OSError:
            continue
    return ""
