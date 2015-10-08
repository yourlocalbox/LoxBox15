#!/bin/bash
for x in epylint pyflakes flake8
do
    python /usr/bin/$x localbox
    python3 /usr/bin/$x localbox
done 
for x in pychecker
do
    /usr/bin/$x localbox
done 

pyreverse localbox
for x in *.dot
do
    dot -Tpdf -O "$x"
done
