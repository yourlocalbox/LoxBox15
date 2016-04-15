# LoxBox15
LocalBox 1.5 rewrite, ook bekend als versie Schimmelpenning
Oudere versies kan men naar verwijzen als 'Willem 2' of 'Uit de tijd van Willem 2'

Nederlandse instalatiegids is te vinden op documentatie/instalatie.md


De volgende documentatie componenten zijn onderdeel van de Localbox:
FO  (Functioneel Ontwerp)
TO  (Technisch Ontwerp)
APH (Applicatie Productie Handleiding)
IH  (Installatie Handleiding)
IP  (ImplementatiePlan)
TP  (TestPlan)

Programmatuur staat in de LocalBox submap op de GitHub. 


TODO: Integriteit geuploade files

[httpd]
certfile = localhost.crt 
keyfile = localhost.key
port = 8001
insecure-http = False

[database]
type = sqlite
filename = database.sqlite3

[filesystem]
bindpoint = /home/nido/localbox/

[logging]
console = True
logfile = ./localbox-log-file.log

[oauth]
verify_url = http://localhost:8000/verify
redirect_url = http://localhost:8000/
direct_back_url = http://localhost/

[cache]
timeout = 600
