LocalBox Instalatiehandleiding
==============================

LocalBox is gedistribueert in verschillende formaten, namelijk 'dumb', 'egg',
'exe' en 'rpm'. 'dumb' en 'egg' zijn twee generieke packages. 'exe' is
windowsspecifiek en rpm hoort bij specifieke linuxdistributies. Een enkel
pakket uit de vier instaleren is voldoende om localbox geinstalleert te krijgen

instalatie dumb package
-----------------------

Het dumb instalatiepakket wordt gedistribueerd met een bestandsnaam als
'localbox-1.8.0.linux-x86_64.tar.gz'. Deze naam impliceert linux-specifiek te
wezen maar gezien er geen C/C++ extensies in LocalBox zitten werkt deze ook voor
Windows en andere abis. Deze file uitpakken levert een directorystructuur op die
rijkt tot ./usr/lib/python2.7/site-packages/localbox/. kopieer deze localbox
directory naar de site-packages directory van uw systeem (bijvoorbeeld
/usr/lib64/python/site-packages) en de instalatie van puur localbox is klaar.

instalatie egg pacakge
----------------------

Het 'egg' installatiepakket wordt gedistribueerd met een bestandsnaam als
'localbox-1.8.0-py2.7.egg'. De naam impliceert dat het python-2.7 specifiek
is, maar deze code is ook bruikbaar onder python3. Gebruik dit file als argument
voor eazy_install. e.g.: 'easy-install /path/to/localbox-1.8.0-py2.7.egg'. 

instalatie rpm package
----------------------

Het 'rpm' instalatiepakket wordt gedistribueert met een bestandsnaam als
'localbox-1.8.0-1.noarch.rpm'. Hoewel de code uit deze file geextraheert kan
worden is het aan te raden deze package alleen met rpm distributies te
gebruiken. Afhankelijk van welke distributie gebruit wordt dient deze
geinstalleerd te worden via 'yum install localbox-1.8.0-1.noarch.rpm' of
'dnf install localbox-1.8.0-1.noarch.rpm'


instalatie windows package
--------------------------

WAARSCHUWING: Hoewel er geen technische reden zijn waarom deze server niet
onder windows zou werken is dit niet uitvoerig getest. Tenzij je precies weet
wat je doet is het ten strengste aan te raden localbox op een unixlike systeem
te instaleren.

Het windows instalatiepakket wordt gedistribueert met een bestandsnaam als
'localbox-1.8.0.linux-x86_65.exe'. Ondanks dat deze filename doet vermoeden dat
dit een linux installer is gaat het hier toch echt om de windows installer.
Uitvoeren van deze file start een InstallShield Wizard. Na enkele keren op
'next' te hebben gedrukt en het pythonpath (normaal iets van "C:\python34\")
te hebben opgegeven is de instalatie compleet.


configuratie
============
TODO: Windows ini file paden.

Nadat LocalBox geinstalleerd is moet het nog geconfigureerd worden. LocalBox
laad na elkaar de ini files in op de locaties '/etc/localbox.ini',
'~/localbox.ini', '~/.config/localbox/config.ini' en 'localbox.ini'. In deze
files horen name = value paren opgedeeld in secties in vishaken ([]).
Onderstaand uitleg van de verschillende secties in de config file.

[httpd]
-------
port = poort op welke localbox beschikbaar is via het netwerk.
insecure-http = flag welke geactiveert kan worden om niet-https verbindingen
        toe te staan. Merk op dat als deze geactiveert is de veiligheid van de
        LocalBox server niet gewaarborgd kan worden. Gebruik dit alleen voor
        debugging, niet voor productie.
certfile = path naar certificaat voor gebruik door de HTTP server voor HTTPS.
keyfile = path naar sleutel voor gebruik van HTTPS op de HTTP server.

[database]
----------
type = 'sqlite' voor een sqlite filedatabase, 'mysql' voor een mysql database
filename = filename voor de sqlite database, alleen nodig voor sqlite databases
hostname = hostname voor de mysql database, alleen nodig voor mysql databases
username = username voor de mysql database, alleen nodig voor mysql databases
password = password voor de mysql database, alleen nodig voor mysql databases
port = port voor de mysql database, alleen nodig voor mysql databases

[filesystem]
------------
bindpoint = directory waar de localbox files opgeslagen worden. In deze
        directory worden folders aangemaakt gebaseerd op de gebruikersnamen met
        hieronder hun eigen directorystructuur.

[logging]
---------
console = wanneer deze op 'True' staat wordt logging ook op standard out geprint
logfile = pad naar file waarin logs worden opgeslagen. 


[loauth]
--------
verify_url = url waarmee localbox de authenticiteit van een gebruiker kan
        verifieren en de gebruikersnaam achterhalen.

[cache]
-------
timeout = hoe lang (in secondes) succesvolle authenticatie wordt gecached.


Gebruik
=======
Het programma is te starten door de localbox module in python te laden. De
makkelijkste mannier is het commando 'python -m localbox'.
TODO: We kunnen/moeten ook nog init-scripts voor localbox maken zodat men
'service start localbox' kan draaien en dat het dan "gewoon werkt" zoals alle
andere services op een unixsysteem.


dependencies
============
Een van de dependencies van localbox is de 'loauth' authorisatieserver.
Instalatie en configuratie van deze gaat analoog aan de LocalBox server.

Indien een MySQL database gebruikt wordt is er ook een dependency op
MySQL-python welk via https://pypi.python.org/pypi/MySQL-python/1.2.5 te vinden
is.
