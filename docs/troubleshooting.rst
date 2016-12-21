***************
Troubleshooting
***************


Permission denied: proxy: HTTPS: attempt to connect to 127.0.0.1:5001 (localhost) failed
========================================================================================

If you are using Apache as a reverse proxy and you catch this error on ``ssl_error_log``, run:

.. code-block:: bash

    setsebool -P httpd_can_network_connect 1

Then restart Apache.