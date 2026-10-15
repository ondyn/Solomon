#!/usr/bin/env sh

set -eu

for catalog in "$1"/*/*/locale/*/LC_MESSAGES/*.po; do
    [ -f "$catalog" ] || continue
    msgfmt --check-format "$catalog" -o "${catalog%.po}.mo"
done
