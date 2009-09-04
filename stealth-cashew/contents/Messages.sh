#! /usr/bin/env bash

NAME="now-rocking"
XGETTEXT="xgettext -ki18n"
EXTRACTRC="extractrc"

if [ "x$1" != "x" ]; then
    if [ ! -d "locale/$1" ]; then
        mkdir -p "locale/$1/LC_MESSAGES"
    fi
fi

$EXTRACTRC ui/*.ui config/*.xml > ./rc.rb
$XGETTEXT rc.rb code/*.rb -o "$NAME.pot"
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

rm -f rc.rb
rm -f now-rocking.pot
