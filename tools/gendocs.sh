#!/bin/bash
if "$1"
then
PTH="$1"
else
PTH="localbox"
fi
doxygen Doxyfile
pyreverse $PTH
for x in *.dot
do
  dot -O -Tpdf $x
done
