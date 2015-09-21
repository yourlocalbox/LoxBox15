"""
LocalBox main initialization class.
"""
from ssl import wrap_socket
try:
    from BaseHTTPServer import BaseHTTPRequestHandler
    from BaseHTTPServer import HTTPServer
except(ImportError) as e:
    from http.server import BaseHTTPRequestHandler
    from http.server import HTTPServer
from .api import ROUTING_LIST
from .config import ConfigSingleton



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
        for regex, function in ROUTING_LIST:
            print("Matching" + self.path + " with pattern " + regex.pattern)
            if regex.match(self.path):
                function(self)

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
    certfile = configparser.get('httpd', 'certfile')
    keyfile = configparser.get('httpd', 'keyfile')
    port = int(configparser.get('httpd', 'port'))
    server_address = ('', port)
    httpd = HTTPServer(server_address, LocalBoxHTTPRequestHandler)
    httpd.socket = wrap_socket(httpd.socket, server_side=True,
                               certfile=certfile, keyfile=keyfile)
    print("ready")
    httpd.serve_forever()
