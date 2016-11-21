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


Dependencies
------------
.. code-block:: bash

    python-mysqldb
    python-oauth         
    python-oauth2client  
    python-oauthlib
