#!/bin/sh
# For maintainers: refresh messages.pot from the source code and merge new
# texts into all .po files (needs gettext: sudo apt install gettext).
set -eu
cd "$(dirname "$0")/.."
LOC=mehrfach_umbenennen/locale
xgettext --language=Python --keyword=_ --from-code=UTF-8 --package-name=mehrfach-umbenennen \
    --no-wrap --sort-output --add-comments -o "$LOC/messages.pot" mehrfach_umbenennen/*.py
for po in "$LOC"/*.po; do
    msgmerge --quiet --update --backup=none --no-wrap "$po" "$LOC/messages.pot"
    printf '%s: ' "$(basename "$po")"
    msgfmt --statistics -o /dev/null "$po"
done
