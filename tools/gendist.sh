#!/bin/bash
python setup.py bdist_dumb
python setup.py bdist_egg
python setup.py bdist_wininst
#python setup.py bdist_rpm

cp dist/localbox-1.8.0.tar.gz ~/rpmbuild/SOURCES
cp conf/localbox.inuit.d ~/rpmbuild/SOURCES
rpmbuild -ba conf/localbox.spec && cp ~/rpmbuild/RPMS/*/localbox*.rpm .

