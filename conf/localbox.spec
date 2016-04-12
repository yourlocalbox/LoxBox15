Name:		localbox
BuildArch:	noarch
Version:	1.8.0
Release:	rc0%{?dist}
License:	EUGPL
URL:		http://www.libbit.eu/nl/producten-nl/localbox
Source0:	localbox-1.8.0.tar.gz
Source1:	localbox.init.d
Summary:	A secure way of sharing documents
Group:		Applications/Publishing
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

%package python
Summary:	A secure way of sharing documents
Group:		Applications/Publishing
Requires:	python
%package python3
Summary:	A secure way of sharing documents
Group:		Applications/Publishing
Requires:	python3

%description
Een nieuwe ontwikkeling betreft LocalBox; een door de overheid gewenst
Dropbox alternatief, veilig, toepasbaar in private cloud omgevingen en
te gebruiken vanaf verschillende devices (iPad, Android en Windows
desktops). 

%description python
Een nieuwe ontwikkeling betreft LocalBox; een door de overheid gewenst
Dropbox alternatief, veilig, toepasbaar in private cloud omgevingen en
te gebruiken vanaf verschillende devices (iPad, Android en Windows
desktops). python2 versie

%description python3
Een nieuwe ontwikkeling betreft LocalBox; een door de overheid gewenst
Dropbox alternatief, veilig, toepasbaar in private cloud omgevingen en
te gebruiken vanaf verschillende devices (iPad, Android en Windows
desktops). python3 versie

%prep
%setup -q

%clean
rm -rf $RPM_BUILD_ROOT

%build python
python3 setup.py build
python setup.py build

%install
mkdir -p $RPM_BUILD_ROOT/etc/init.d
mkdir -p /usr/share/localbox
cat %{SOURCE1} | sed "s/python/python3/g" > $RPM_BUILD_ROOT/etc/init.d/localbox.python3
install %{SOURCE1} $RPM_BUILD_ROOT/etc/init.d/localbox.python
python3 setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%pre
getent group localbox || groupadd -r localbox
getent passwd localbox || useradd -r -g localbox -d /usr/share/localbox -s /sbin/nologin -c "Localbox server user account"

%post

%files python
%attr(0755, localbox, localbox) /usr/share/localbox
%attr(0644, root, root) /etc/init.d/localbox.python
%attr(0644, root, root) /usr/lib/python2.7/site-packages/localbox-%{version}-py2.7.egg-info/*
%attr(0644, root, root) /usr/lib/python2.7/site-packages/localbox/*.py
%attr(0644, root, root) /usr/lib/python2.7/site-packages/localbox/*.pyc
%attr(0644, root, root) /usr/lib/python2.7/site-packages/localbox/*.pyo
%files python3
%attr(0755, localbox, localbox) /usr/share/localbox
%attr(0644, root, root) /etc/init.d/localbox.python3
%attr(0644, root, root) /usr/lib/python3.4/site-packages/localbox-%{version}-py3.4.egg-info/*
%attr(0644, root, root) /usr/lib/python3.4/site-packages/localbox/*.py
%attr(0644, root, root) /usr/lib/python3.4/site-packages/localbox/__pycache__/*.pyc
%attr(0644, root, root) /usr/lib/python3.4/site-packages/localbox/__pycache__/*.pyo
