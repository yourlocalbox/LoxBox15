import os
from OpenSSL import crypto
from socket import gethostname

from localbox import config

CERT_FILE = "selfsigned.crt"
KEY_FILE = "private.key"


def get_bindpoint():
    bindpoint = os.path.expandvars(config.get('filesystem', 'bindpoint'))
    return bindpoint


def get_logging_empty_extra():
    return {'user': None, 'ip': None, 'path': None}


def get_logging_extra(request_handler):
    return {'user': request_handler.user, 'ip': request_handler.client_address[0], 'path': request_handler.path}


def create_self_signed_cert():
    # create a key pair
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 1024)

    # create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = "UK"
    cert.get_subject().ST = "London"
    cert.get_subject().L = "London"
    cert.get_subject().O = "Dummy Company Ltd"
    cert.get_subject().OU = "Dummy Company Ltd"
    cert.get_subject().CN = gethostname()
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha1')

    open(CERT_FILE, "wt").write(
        crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    open(KEY_FILE, "wt").write(
        crypto.dump_privatekey(crypto.FILETYPE_PEM, k))


def get_ssl_cert():
    certfile = config.get('httpd', 'certfile')
    keyfile = config.get('httpd', 'keyfile')

    # TODO: if not exits(certfile) create_self_signed_cert()
    return (certfile, keyfile)
