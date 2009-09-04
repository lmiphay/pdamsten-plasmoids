#!/bin/bash

rm -f *.plasmoid
for dir in $(find . -maxdepth 1 -mindepth 1 -type d); do
    dir=${dir:2}
    if [ "$dir" == ".git" ]; then
        continue
    fi
    cd $dir
    zip -9 -v -o -r ../$dir.plasmoid * -x \*~
    cd ..
done
