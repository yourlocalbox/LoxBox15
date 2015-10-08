#!/bin/bash
for x in epylint pyflakes flake8
do
    python /usr/bin/$x localbox
    python3 /usr/bin/$x localbox
done 
for x in pychecker
do
    bash /usr/bin/$x localbox
done 
