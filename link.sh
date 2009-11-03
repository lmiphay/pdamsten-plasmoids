#!/bin/bash

if [[ "$KDEHOME" == "" ]]; then
  KDEHOME="$HOME/.kde"
fi

for desktop in ./*/*.desktop; do
    DIR=$(basename $(dirname $desktop))
    NAME=$(grep PluginInfo-Name $DIR/metadata.desktop | sed s/.*=//)
    cp "$desktop" "$KDEHOME/share/kde4/services/plasma-applet-$NAME.desktop"
    if [[ ! -e "$KDEHOME/share/apps/plasma/plasmoids/$NAME" ]]; then
        ln -s "$(pwd)/$DIR/" "$KDEHOME/share/apps/plasma/plasmoids/$NAME"
    fi
done

