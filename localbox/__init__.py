"""
LocalBox main initialization class.
"""
from ssl import wrap_socket
try:
    halter = raw_input
except NameError:
    # raw_input does not exist in python3, but input does, so in both python2 and
    # python3 we are now able to use the 'input()' funcion.
    halter = input


try:
    from BaseHTTPServer import BaseHTTPRequestHandler
    from BaseHTTPServer import HTTPServer
except ImportError:
    from http.server import BaseHTTPRequestHandler
    from http.server import HTTPServer
from .api import ROUTING_LIST
from .config import ConfigSingleton
from .files import SymlinkCache


def authentication_dummy():
    """
    return the string 'user' and pretend authentication happened
    """
    return "user"


class LocalBoxHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    class extending the BaseHTTPRequestHandler and handling the HTTP requests
    in do_POST and do_GET (which in their turn forward said requests to
    do_request)
    """
    def do_request(self):
        """
        Handle a request (do_POST and do_GET both forward to this function)
        """
        print("processing "+ self.path)
        self.user = authentication_dummy()
        if not self.user:
            print("authentication problem")
            return
        match_found = False
        print "Finding " + self.path
        for regex, function in ROUTING_LIST:
            if regex.match(self.path):
                print("Matching " + self.path + " with pattern " + regex.pattern)
                match_found = True
                function(self)
                break
        if not match_found:
            print("Could not match thhe path: "+ self.path)

    def do_POST(self):
        """
        handle a POST request
        """
        self.do_request()


    def do_GET(self):
        """
        handle a POST request
        """
        self.do_request()


def main():
    """
    run the actual LocalBox Server
    """
    configparser = ConfigSingleton()
    SymlinkCache()
    port = int(configparser.get('httpd', 'port', 443))
    insecure_mode = configparser.getboolean('httpd', 'insecure-http', default=False)
    server_address = ('', port)
    httpd = HTTPServer(server_address, LocalBoxHTTPRequestHandler)
    if insecure_mode:
        print("WARNING: Running Insecure HTTP.")
        print("WARNING: Therefore, SSL has not been enabled.")
        print("WARNING: Therefore, THIS SERVER IS NOT SECURE!!!.")
        halter("Press a key to continue.")
    else:
        certfile = configparser.get('httpd', 'certfile')
        keyfile = configparser.get('httpd', 'keyfile')
        httpd.socket = wrap_socket(httpd.socket, server_side=True,
                                   certfile=certfile, keyfile=keyfile)
    print("ready")
    httpd.serve_forever()
