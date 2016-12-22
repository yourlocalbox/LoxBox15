"""
LocalBox main initialization class.
"""
from logging import getLogger
from os import remove
from os.path import join
from shutil import rmtree
from ssl import wrap_socket
from sys import argv

from loxcommon.config import ConfigSingleton

config = ConfigSingleton('localbox')

import localbox.utils as lb_utils
from localbox.auth import authorize
from localbox.files import create_user_home
from localbox.utils import get_bindpoint, get_ssl_cert

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

try:
    HALTER = raw_input  # pylint: disable=E0602
except NameError:
    # raw_input does not exist in python3, but input does, so in both python2
    # and python3 we are now able to use the 'input()' function.
    HALTER = input

try:
    from BaseHTTPServer import BaseHTTPRequestHandler
    from BaseHTTPServer import HTTPServer
except ImportError:
    from http.server import BaseHTTPRequestHandler  # pylint: disable=F0401
    from http.server import HTTPServer  # pylint: disable=F0401

from localbox.api import ROUTING_LIST
from .cache import TimedCache
from .files import SymlinkCache
from .database import database_execute


class LocalBoxHTTPRequestHandler(BaseHTTPRequestHandler, object):
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
        self.protocol = "https://" if config.getboolean('httpd', 'insecure-http', True) else "http://"
        self.back_url = config.get('oauth', 'direct_back_url')
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def send_response(self):
        """
        Returns an answer to an HTTPRequest in the proper order of status,
        new_headers, body. Other functions can set these values and this
        function will send it over the line properly.

        :return:
        """
        super(LocalBoxHTTPRequestHandler, self).send_response(self.status)
        for header in self.new_headers:
            self.send_header(header, self.new_headers[header])
        self.end_headers()
        if self.body is not None:
            self.wfile.write(self.body)

    def get_log_dict(self):
        """
        returns a dictionary of 'extra' information from the request for the
        logger. Extra information consists of 'user', 'ip' and 'path', or None
        where this information does not make sense.
        """
        try:
            ip = self.headers['x-forwarded-for']
        except KeyError:
            ip = self.client_address[0]
        extra = {'user': self.user, 'ip': ip, 'path': self.path}
        return extra

    def wrap_request(func):
        def handle(request):
            try:
                getLogger(__name__).info("%s: %s" % (func.__name__, request.path), extra=request.get_log_dict())
                func(request)
            except Exception as ex:
                getLogger(__name__).exception('failed %s: %s' % (func.__name__, ex), extra=request.get_log_dict())
            finally:
                request.send_response()

        return handle

    @wrap_request
    def do_POST(self):
        """
        Handle a POST request (by forwarding it to do_request).

        :return:
        """
        self.do_request()

    @wrap_request
    def do_GET(self):
        """
        handle a POST request (by forwarding it to do_request)
        """
        self.do_request()

    @authorize
    def do_request(self):
        """
        Handle a request (do_POST and do_GET both forward to this function).
        Handling of a requests is done in three phases. First, the
        authorization is checked. When this is in order, the ROUTING_LIST is
        consulted to find the function to do the actual work. After this
        function has executed, the request is responded using send_response.
        """
        log = getLogger('api')
        # Log headers
        map(lambda k: log.debug('Header: %s: %s' % (k, self.headers[k]), extra=self.get_log_dict()), self.headers)

        match_found = False
        for regex, function in ROUTING_LIST:
            if regex.match(self.path):
                log.info("Running " + function.__name__ + " on " + self.path +
                         " for " + self.user, extra=self.get_log_dict())

                match_found = True

                create_user_home(self.user)
                self.read_request_body()
                function(self)
                break
        if not match_found:
            log.debug("Could not match the path: " + self.path, extra=self.get_log_dict())

    def read_request_body(self):
        """
        Read data from request.

        :return:
        """
        length = int(self.headers.get('content-length', 0))
        if length:
            getLogger(__name__).debug("reading %s bytes..." % length, extra=self.get_log_dict())
        self.old_body = ""
        file_str = StringIO()
        max_read_size = 65536
        while length > 0:
            read_size = min(max_read_size, length)
            file_str.write(self.rfile.read(read_size))
            length -= read_size
        self.old_body = file_str.getvalue()
        if self.body is None:
            self.body = ""


def main():
    """
    run the actual LocalBox Server. Initialises the symlink cache, starts a
    HTTPServer and serves requests forever, unless '--test-single-call' has
    been specified as command line argument
    """
    symlinkcache = SymlinkCache()
    try:
        position = argv.index("--clear-user")
        user = argv[position + 1]
        user_folder = join(
            config.get('filesystem', 'bindpoint'), user)
        getLogger('api').info(
            "Deleting info for user " + user, extra={'ip': 'cli', 'user': user})
        for sqlstring in 'delete from users where name = ?', 'delete from keys where user = ?', 'delete from invitations where sender = ?', 'delete from invitations where receiver = ?', 'delete from shares where user = ?':
            database_execute(sqlstring, (user,))
        for symlinkdest in symlinkcache:
            if symlinkdest.startswith(user_folder):
                symlinks = symlinkcache.get(symlinkdest)
                for symlink in symlinks:
                    remove(symlink)
        rmtree(user_folder)
        return
    except (ValueError, IndexError):
        port = int(config.get('httpd', 'port', 443))
        insecure_mode = config.getboolean('httpd', 'insecure-http', default=False)
        server_address = ('', port)
        httpd = HTTPServer(server_address, LocalBoxHTTPRequestHandler)
        if insecure_mode:
            getLogger(__name__).warn('Running Insecure HTTP')
            getLogger(__name__).warn('Therefore, SSL has not been enabled.')
            getLogger(__name__).warn('WARNING: Therefore, THIS SERVER IS NOT SECURE!!!')
            if "--test-single-call" not in argv:
                HALTER("Press a key to continue.")
        else:
            certfile, keyfile = get_ssl_cert()
            httpd.socket = wrap_socket(httpd.socket, server_side=True, certfile=certfile, keyfile=keyfile)

        getLogger().info("Server ready", extra={'user': None, 'ip': None, 'path': None})

        if "--test-single-call" in argv:
            httpd.handle_request()
        else:
            httpd.serve_forever()
