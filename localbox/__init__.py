"""
LocalBox main initialization class.
"""
from cStringIO import StringIO
from ssl import wrap_socket
from logging import getLogger
from sys import argv
from os import mkdir
from os import remove
from os.path import join
from os.path import exists
try:
    from urllib2 import Request
    from urllib2 import urlopen
    from urllib2 import HTTPError
    from urllib import urlencode  # pylint: disable=E0611
except ImportError:
    from urllib.request import Request  # pylint: disable=E0611,F0401
    from urllib.request import urlopen  # pylint: disable=E0611,F0401
    from urllib.error import HTTPError  # pylint: disable=E0611,F0401
    from urllib.parse import urlencode  # pylint: disable=E0611,F0401


try:
    HALTER = raw_input  # pylint: disable=E0602
except NameError:
    # raw_input does not exist in python3, but input does, so in both python2
    # and python3 we are now able to use the 'input()' funcion.
    HALTER = input


try:
    from BaseHTTPServer import BaseHTTPRequestHandler
    from BaseHTTPServer import HTTPServer
except ImportError:
    from http.server import BaseHTTPRequestHandler  # pylint: disable=F0401
    from http.server import HTTPServer  # pylint: disable=F0401


from .api import ROUTING_LIST
from .cache import TimedCache
from .config import ConfigSingleton
from .files import SymlinkCache
from .database import database_execute


class LocalBoxHTTPRequestHandler(BaseHTTPRequestHandler):

    """
    class extending the BaseHTTPRequestHandler and handling the HTTP requests
    in do_POST and do_GET (which in their turn forward said requests to
    do_request)
    """

    def __init__(self, request, client_address, server):
        self.user = None
        self.new_headers = {}
        self.body = None
        self.old_body = None
        self.status = 500
        self.protocol = ""
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def check_authorization(self):
        """
        assert whether the authorization header is valid by checking it against
        the cache first and if unsuccesful, the oauth server. Sets the 'user'
        field when succesful and returns said name. returns None on failure
        """
        auth_header = self.headers.getheader('Authorization')
        if auth_header is None:
            return None
        config = ConfigSingleton()
        auth_url = config.get('oauth', 'verify_url')
        time_out = config.get('cache', 'timeout')
        cache = TimedCache(timeout=0)  # Cache is broken
        name = cache.get(auth_header)
        if name is not None:
            return name
        request = Request(auth_url, None, {'Authorization': auth_header})
        try:
            response = urlopen(request)
            name = response.read()
        except HTTPError as error:
            if error.code == 403:
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
            self.send_header(header, self.new_headers[header])
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
        print("DoingRequest")
        max_read_size = 65536
        log = getLogger('api')
        length = int(self.headers.get('content-length', 0))
        self.old_body = ""
        file_str = StringIO()
        while length > 0:
            read_size = min(max_read_size, length)
            print(
                str(max_read_size) + "\t" + str(length) + "\t" + str(read_size))
            file_str.write(self.rfile.read(read_size))
            length -= read_size
        print("done")
        self.old_body = file_str.getvalue()
        print("copied")
        if self.body is None:
            self.body = ""
        #log.debug(self.command + " " + self.path + "\n" + str(self.headers) + "\n\n" + self.old_body, extra=self.get_log_dict())
        config = ConfigSingleton()
        self.protocol = "https://"
        if config.getboolean('http', 'insecure-http', True):
            self.protocol = "http://"
        back_url = config.get('oauth', 'direct_back_url')
        if back_url:
            querystring = urlencode({'redirect_uri': back_url})
        else:
            querystring = urlencode({'redirect_uri': self.protocol +
                                     self.headers['Host'] + self.path})
        #self.user = authentication_dummy()
        self.user = self.check_authorization()

        if not self.user:
            log.debug("authentication problem", extra=self.get_log_dict())
            self.status = 401
            redirect_url = config.get('oauth', 'redirect_url') + "?" + \
                querystring
            self.new_headers[
                'WWW-Authenticate'] = 'Bearer domain="' + redirect_url + '"'
            self.body = "<h1>401: Forbidden.</h1>" \
                        "<p>Authorization failed. Please authenticate at" \
                        '<a href="?">?</a></p>' % (redirect_url,
                                                   redirect_url)
            self.send_request()
            return
        user_folder = join(
            ConfigSingleton().get('filesystem', 'bindpoint'), self.user)
        if not exists(user_folder):
            mkdir(user_folder)
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
        #log.debug(str(self.status) + " " +  str(self.new_headers) + "\n\n" + str(self.body), extra=self.get_log_dict())

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
    symlinkcache = SymlinkCache()
    try:
        position = argv.index("--clear-user")
        user = argv[position + 1]
        user_folder = join(configparser.get('filesystem', 'bindpoint'), user)
        log = getLogger('api').info(
            "Deleting info for user " + user, extra={'ip': 'cli', 'user': user})
        for sqlstring in 'delete from users where name = ?', 'delete from keys where user = ?', 'delete from invitations where sender = ?',  'delete from invitations where receiver = ?', 'delete from shares where user = ?':
            database_execute(sqlstring, (user,))
        for symlinkdest in symlinkcache:
            if symlink.startswith(user_folder):
                symlinks = symlinkcache.get(symlinkdest)
                for symlink in symlinks:
                    remove(symlink)
        rmtree(user_folder)
        return
    except (ValueError, IndexError):
        pass
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
                HALTER("Press a key to continue.")
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
