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
    git clone https://github.com/2EK/LoxBox15.git
    git clone https://github.com/wilson-santos-pf/LoxCommon.git
    cd LoxBox15
    git checkout develop


Install loauth backend server
-----------------------------
.. code-block:: bash

    cd ~
    git clone https://github.com/2EK/loauth.git
    cd loauth
    git checkout develop
    python -m loauth --init-db
    python -m loauth --add-user <USERNAME>


Dependencies
------------
.. code-block:: bash

    python-mysqldb
    python-oauth         
    python-oauth2client  
    python-oauthlib

