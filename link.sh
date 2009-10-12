#!/bin/bash

if [[ "$KDEHOME" == "" ]]; then
  KDEHOME="$HOME/.kde"
fi

for desktop in ./*/*.desktop; do
    NAME=$(basename $(dirname $desktop))
    cp "$desktop" "$KDEHOME/share/kde4/services/plasma-applet-$NAME.desktop"
    if [[ ! -e "$KDEHOME/share/apps/plasma/plasmoids/$NAME" ]]; then
        ln -s "$(pwd)/$NAME/" "$KDEHOME/share/apps/plasma/plasmoids/$NAME"
    fi
done

