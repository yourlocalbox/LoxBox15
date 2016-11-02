*************
Configuration
*************

Before running the server, two configuration files must be edit: ``localbox.ini`` and loauth.ini.


localbox.ini
============

[httpd]
-------

port
++++
Port for running the service. Example: 5000


[filesystem]
------------

bindpoint
+++++++++
Location for the files that the users are syncing. Example: /home/$USER/localbox-users

[logging]
---------

console
+++++++
Example: True

logfile
+++++++
Example: ./localbox-log-file.log

format
++++++
Example: %(asctime)s %(module)10s %(lineno)4s IP:%(ip)20s User:%(user)10s %(levelname)8s %(message)s


[cache]
-------

timeout
+++++++
Example: 600


[oauth]
-------

verify_url
++++++++++
When the user has an access token it is validated using this URL. Example: http://localhost:5000/verify

redirect_url
++++++++++++
When the user is not authenticated he is redirected to this URL. Example: http://localhost:5000/loauth


loauth.ini
==========

[httpd]
-------

port
++++
Port for running the service. Example: 5001

