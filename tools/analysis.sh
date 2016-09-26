#!/bin/bash
if "$1"
then
PTH="$1"
else
PTH="localbox"
fi

for x in epylint pyflakes flake8
do
    python /usr/bin/$x "$PTH"
    python3 /usr/bin/$x "$PTH"
done 
for x in pychecker
do
    /usr/bin/$x "$PTH"
done 

pyreverse localbox
for x in *.dot
do
    dot -Tpdf -O "$x"
done
