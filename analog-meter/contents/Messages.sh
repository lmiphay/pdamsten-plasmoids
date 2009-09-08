#! /usr/bin/env bash

NAME="analog-meter"
SCRIPTLANG="py"

XGETTEXT="xgettext --from-code=UTF-8 -kde -ci18n -ki18n:1 -ki18nc:1c,2 -ki18np:1,2 \
          -ki18ncp:1c,2,3 -ktr2i18n:1 -kI18N_NOOP:1 -kI18N_NOOP2:1c,2 -kaliasLocale \
          -kki18n:1 -kki18nc:1c,2 -kki18np:1,2 -kki18ncp:1c,2,3xgettext -ki18n -ki18nc
          -ki18ncp -ki18np"
EXTRACTRC="extractrc"

if [ "x$1" != "x" ]; then
    if [ ! -d "locale/$1" ]; then
        mkdir -p "locale/$1/LC_MESSAGES"
    fi
fi

$EXTRACTRC ui/*.ui config/*.xml > ./rc.$SCRIPTLANG
$XGETTEXT rc.$SCRIPTLANG code/*.$SCRIPTLANG -o "$NAME.pot"
sed -e 's/charset=CHARSET/charset=UTF-8/g' -i "$NAME.pot"

for d in locale/*; do
    if [ -d "$d" ]; then
        if [ -f "$d/LC_MESSAGES/$NAME.po" ]; then
            echo "Merging $NAME.pot -> $d/LC_MESSAGES/$NAME.po ..."
            msgmerge -U "$d/LC_MESSAGES/$NAME.po" "$NAME.pot"
        else
            echo "Copying $NAME.pot -> $d/LC_MESSAGES/$NAME.po ..."
            cp "$NAME.pot" "$d/LC_MESSAGES/$NAME.po"
        fi
    fi
done

for d in locale/*; do
    echo "Making $d/LC_MESSAGES/$NAME.mo ..."
    msgfmt "$d/LC_MESSAGES/$NAME.po" -o "$d/LC_MESSAGES/$NAME.mo"
done

rm -f rc.$SCRIPTLANG
rm -f $NAME.pot
