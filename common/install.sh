#!/bin/bash

# git does not preserve hard links and plasma cannot read ui files from symlinks
# so copy files until better solution

FILES=(
"analog-meter/contents/ui/add.ui"
"analog-meter/contents/code/add.py"
"analog-meter/contents/code/helpers.py"
"complex-plotter/contents/ui/add.ui"
"complex-plotter/contents/code/add.py"
"complex-plotter/contents/code/helpers.py"
)

SCRIPT=$(cd "${0%/*}" 2>/dev/null; echo "$PWD"/"${0##*/}")
DIR=$(dirname "$SCRIPT")

for FILE in "${FILES[@]}"; do
    SOURCE=$(basename $FILE)
    cp "$SOURCE" "../$FILE"
done