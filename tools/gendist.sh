#!/bin/bash
python setup.py bdist_dumb
python setup.py bdist_egg
python setup.py bdist_rpm
python setup.py bdist_wininst
