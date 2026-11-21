#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# For maintainers: refresh messages.pot from the source code and merge new
# texts into all .po files (needs gettext: sudo apt install gettext).
set -eu
cd "$(dirname "$0")/.."
LOC=linux_speed_rename/locale
xgettext --language=Python --keyword=_ --from-code=UTF-8 --package-name=linux-speed-rename \
    --no-wrap --sort-output --add-comments -o "$LOC/messages.pot" linux_speed_rename/*.py
for po in "$LOC"/*.po; do
    msgmerge --quiet --update --backup=none --no-wrap --no-fuzzy-matching "$po" "$LOC/messages.pot"
    msgattrib --no-obsolete --no-wrap -o "$po" "$po"
    printf '%s: ' "$(basename "$po")"
    msgfmt --statistics -o /dev/null "$po"
done
