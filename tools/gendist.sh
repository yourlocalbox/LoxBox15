#!/bin/bash -x
python setup.py bdist_dumb
python setup.py bdist_egg
python setup.py bdist_wininst
#python setup.py bdist_rpm

archivename=`cat conf/localbox.spec | grep "Source0:" | sed "s/Source0:[ \t]\+//"`
git archive --format=tar.gz --prefix=localbox-1.8.0/ -o "dist/$archivename" HEAD

cp dist/localbox-1.8.0.tar.gz ~/rpmbuild/SOURCES
cp conf/localbox.init.d ~/rpmbuild/SOURCES
rpmbuild -ba conf/localbox.spec && cp ~/rpmbuild/RPMS/*/localbox*.rpm dist
