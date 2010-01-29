#!/bin/bash

if [[ "$KDEHOME" == "" ]]; then
  KDEHOME="$HOME/.kde"
fi

for desktop in ./*/*.desktop; do
    DIR=$(basename $(dirname $desktop))
    desktop=$(echo $desktop | sed -e "s:\./::")
    NAME=$(grep PluginInfo-Name $DIR/metadata.desktop | sed s/.*=//)
    TYPE=$(grep ServiceTypes $DIR/metadata.desktop | \
           sed -e "s:X-KDE-ServiceTypes=Plasma/::g" \
               -e "s/Popup//g" | \
           tr "[:upper:]" "[:lower:]")
    EXT=$(echo $TYPE | sed -e "s/applet/plasmoid/g")
    echo $desktop $DIR $NAME $EXT $TYPE
    rm -f "$KDEHOME/share/kde4/services/plasma-$TYPE-$NAME.desktop"
    ln -s "$(pwd)/$desktop" "$KDEHOME/share/kde4/services/plasma-$TYPE-$NAME.desktop"
    rm -fR "$KDEHOME/share/apps/plasma/$EXT""s/$NAME"
    if [ ! -d "$KDEHOME/share/apps/plasma/$EXT""s/" ]; then
        mkdir -p "$KDEHOME/share/apps/plasma/$EXT""s/"
    fi
    ln -s "$(pwd)/$DIR/" "$KDEHOME/share/apps/plasma/$EXT""s/$NAME"
done

