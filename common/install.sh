#!/bin/bash

# git does not preserve hard links and plasma cannot read ui files from symlinks
# so copy files until better solution

FILES=(
"analog-meter/contents/Messages.sh"
"analog-meter/contents/ui/add.ui"
"analog-meter/contents/code/add.py"
"analog-meter/contents/code/helpers.py"
"complex-plotter/contents/Messages.sh"
"complex-plotter/contents/ui/add.ui"
"complex-plotter/contents/code/add.py"
"complex-plotter/contents/code/helpers.py"
"now-rocking/contents/Messages.sh"
"now-rocking/contents/code/helpers.py"
"scriptedimage/contents/Messages.sh"
"stealth-cashew/contents/Messages.sh"
"day-and-night/contents/code/wallpapercache.py"
"clock/contents/code/wallpapercache.py"
"day-and-night/contents/code/backgrounddelegate.py"
"clock/contents/code/backgrounddelegate.py"
"clock/contents/code/helpers.py"
)

SCRIPT=$(cd "${0%/*}" 2>/dev/null; echo "$PWD"/"${0##*/}")
DIR=$(dirname "$SCRIPT")
PLASMOIDSDIR=$(dirname "$DIR")

for FILE in "${FILES[@]}"; do
    SOURCE=$(basename $FILE)
    if ! cmp --silent "$DIR/$SOURCE" "$PLASMOIDSDIR/$FILE" ; then
        echo "$DIR/$SOURCE" " => " "$PLASMOIDSDIR/$FILE"
        cp "$DIR/$SOURCE" "$PLASMOIDSDIR/$FILE"
    fi
done