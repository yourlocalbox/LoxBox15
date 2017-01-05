import socket

LOAUTH_PORT = 5000
VERIFY_URL = 'http://%s:%d/verify' % (socket.gethostname(), LOAUTH_PORT)
REDIRECT_URL = 'http://%s:%s/loauth/' % (socket.gethostname(), LOAUTH_PORT)
DIRECT_BACK_URL = 'http://%s' % socket.gethostname()
