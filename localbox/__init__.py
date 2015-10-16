"""
LocalBox main initialization class.
"""
from ssl import wrap_socket
from logging import getLogger
from sys import argv
try:
    from urllib2 import Request
    from urllib2 import urlopen
    from urllib2 import HTTPError
    from urllib import urlencode
except ImportError:
    from urllib.request import Request  # pylint: disable=E0611,F0401
    from urllib.request import urlopen  # pylint: disable=E0611,F0401
    from urllib.error import HTTPError  # pylint: disable=E0611,F0401
    from urllib.parse import urlencode  # pylint: disable=E0611,F0401


try:
    halter = raw_input  # pylint: disable=E0602
except NameError:
    # raw_input does not exist in python3, but input does, so in both python2
    # and python3 we are now able to use the 'input()' funcion.
    halter = input


try:
    from BaseHTTPServer import BaseHTTPRequestHandler
    from BaseHTTPServer import HTTPServer
except ImportError:
    from http.server import BaseHTTPRequestHandler  # pylint: disable=F0401
    from http.server import HTTPServer  # pylint: disable=F0401


from .api import ready_cookie
from .api import ROUTING_LIST
from .cache import TimedCache
from .config import ConfigSingleton
from .files import SymlinkCache


def authentication_dummy():
    """
    return the string 'user' and pretend authentication happened. To be
    replaced with actual authentication before delivery. Not part of the final
    codebase
    @return "user"
    """
    return "user"


class LocalBoxHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    class extending the BaseHTTPRequestHandler and handling the HTTP requests
    in do_POST and do_GET (which in their turn forward said requests to
    do_request)
    """
    def __init__(self, request, client_address, server):
        self.user = None
        self.new_headers = []
        self.body = None
        self.status = 500
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def check_authorization(self):
        """
        assert whether the authorization header is valid by checking it against
        the cache first and if unsuccesful, the oauth server. Sets the 'user'
        field when succesful and returns said name. returns None on failure
        """
        auth_header = self.headers.getheader('Authorization')
        config = ConfigSingleton()
        auth_url = config.get('oauth', 'verify_url')
        time_out = config.get('cache', 'timeout')
        cache = TimedCache(timeout=time_out)
        name = cache.get(auth_header)
        if name is not None:
            return name
        request = Request(auth_url, None, {'Authorization': auth_header})
        try:
            response = urlopen(request)
            name = response.read()
        except HTTPError as e:
            if e.code == 403:
                getLogger('auth').debug("Wrong/expired code",
                                        extra=self.get_log_dict())
            name = ''
        if name == '':
            name = None
            getLogger('auth').debug('authentication failed',
                                    extra=self.get_log_dict())
        else:
            getLogger('auth').debug('Authenticated ' + name,
                                    extra=self.get_log_dict())
            cache.add(auth_header, name)
        return name

    def send_request(self):
        """
        Returns an answer to an HTTPRequest in the proper order of status,
        new_headers, body. Other functions can set these values and this
        function will send it over the line properly.
        """
        self.send_response(self.status)
        for header in self.new_headers:
            self.send_header(header[0], header[1])
        self.end_headers()
        if self.body is not None:
            self.wfile.write(self.body)

    def get_log_dict(self):
        """
        returns a dictionary of `extra' information from the request for the
        logger. Extra information consists of 'user', 'ip' and 'path', or None
        where this information does not make sense.
        """
        extra = {'user': self.user, 'ip': self.client_address[0],
                 'path': self.path}
        return extra

    def do_request(self):
        """
        Handle a request (do_POST and do_GET both forward to this function).
        Handling of a requests is done in three phases. First, the
        authorization is checked. When this is in order, the ROUTING_LIST is
        consulted to find the function to do the actual work. After this
        function has executed, the request is responded tousing send_request.
        """
        config = ConfigSingleton()
        protocol = "https://"
        if config.getboolean('http', 'insecure-http', False):
            protocol = "http://"
        querystring = urlencode({'redirect_uri': protocol +
                                self.headers['Host'] + self.path})
        #self.user = authentication_dummy()
        self.user = self.check_authorization()
        ready_cookie(self)
        log = getLogger('api')
        if not self.user:
            log.debug("authentication problem", extra=self.get_log_dict())
            self.status = 403
            redirect_url = config.get('oauth', 'redirect_url') + "?" + \
                querystring
            self.headers['Location'] = redirect_url
            self.body = "<h1>403: Forbidden.</h1>" \
                        "<p>Authorization failed. Please authenticate at" \
                        '<a href="%s">%s</a></p>' % (redirect_url,
                                                     redirect_url)
            self.send_request()
            return
        log.critical("processing " + self.path, extra=self.get_log_dict())
        for key in self.headers:
            value = self.headers[key]
            log.debug("Header: " + key + ": " + value,
                      extra=self.get_log_dict())
        match_found = False
        for regex, function in ROUTING_LIST:
            if regex.match(self.path):
                log.debug("Running " + function.__name__ + " on " + self.path +
                          " for " + self.user, extra=self.get_log_dict())
                match_found = True
                function(self)
                self.send_request()
                break
        if not match_found:
            log.debug("Could not match the path: " + self.path,
                      extra=self.get_log_dict())

    def do_POST(self):
        """
        handle a POST request (by forwarding it to do_request)
        """
        self.do_request()

    def do_GET(self):
        """
        handle a POST request (by forwarding it to do_request)
        """
        self.do_request()


def main():
    """
    run the actual LocalBox Server. Initialises the symlink cache, starts a
    HTTPServer and serves requests forever, unless '--test-single-call' has
    been specified as command line argument
    """
    configparser = ConfigSingleton()
    SymlinkCache()
    port = int(configparser.get('httpd', 'port', 443))
    insecure_mode = configparser.getboolean('httpd', 'insecure-http',
                                            default=False)
    server_address = ('', port)
    httpd = HTTPServer(server_address, LocalBoxHTTPRequestHandler)
    if insecure_mode:
        print("WARNING: Running Insecure HTTP.")
        print("WARNING: Therefore, SSL has not been enabled.")
        print("WARNING: Therefore, THIS SERVER IS NOT SECURE!!!.")
        if "--test-single-call" not in argv:
            halter("Press a key to continue.")
    else:
        certfile = configparser.get('httpd', 'certfile')
        keyfile = configparser.get('httpd', 'keyfile')
        httpd.socket = wrap_socket(httpd.socket, server_side=True,
                                   certfile=certfile, keyfile=keyfile)
    print("ready")

    if "--test-single-call" in argv:
        httpd.handle_request()
    else:
        httpd.serve_forever()
