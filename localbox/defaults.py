import socket

#: port where the Loauth server is listening to requests
LOAUTH_PORT = 5000
#: Loauth URL for verifying if the bearer authorization token is expired
VERIFY_URL = 'http://%s:%d/verify' % (socket.gethostname(), LOAUTH_PORT)
#: Loauth URL for validating authorization request
REDIRECT_URL = 'http://%s:%s/loauth/' % (socket.gethostname(), LOAUTH_PORT)
DIRECT_BACK_URL = 'http://%s' % socket.gethostname()
