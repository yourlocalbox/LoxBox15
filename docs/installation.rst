************
Installation
************

Install from source code
========================

**NOTE:** This assumes that installation is being performed on a Linux system.

Install LocalBox backend server
-------------------------------
.. code-block:: bash

    cd ~
    git clone https://github.com/yourlocalbox/LoxBox15.git
    git clone https://github.com/yourlocalbox/LoxCommon.git
    cd LoxBox15
    python -m localbox


Install loauth backend server
-----------------------------
.. code-block:: bash

    cd ~
    git clone https://github.com/yourlocalbox/loauth.git
    cd loauth
    python -m loauth --init-db
    python -m loauth --add-user <USERNAME>

Setup as service
----------------

Ubuntu >= 15.04
+++++++++++++++
.. code-block:: bash

    sudo cp scripts/localbox.sh /usr/local/bin/ && sudo chmod +x /usr/local/bin/localbox.sh
    sudo cp scripts/localbox.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable localbox.service
    sudo systemctl start localbox

Dependencies
------------
.. code-block:: bash

    python-mysqldb
    python-oauth         
    python-oauth2client  
    python-oauthlib

