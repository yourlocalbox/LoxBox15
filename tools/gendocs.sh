#!/bin/bash
doxygen Doxyfile
pyreverse localbox
for x in *.dot
do
  dot -O -Tpdf $x
done
