"""
LocalBox main initialization class.
"""
from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from json import dumps, JSONEncoder
from re import compile as regex_compile
from ssl import wrap_socket
from urllib import unquote
from api import ROUTING_LIST

from .config import ConfigSingleton
from .database import database_execute

from pprint import pprint


class LocalBoxJSONEncoder(JSONEncoder):
    """
    JSONEncoder for localbox classes
    """
    def default(self, o):
        """
        The way objects are usually encoded into JSON.
        """
        if hasattr(o, 'to_json'):
            return o.to_json()
        return o.__dict__


class User(object):
    """
    User object, limited to more or less the 'name' only, given how the actual
    user administration is done by the authentication mechanism.
    """
    def __init__(self, name=None):
        self.name = name

    def to_json(self):
        """
        Method to turn an object into JSON.
        """
        return {'id': self.name, 'title': self.name, 'type': 'user'}


class Group(object):
    """
    Underdefined group object which due to lack of user administration will
    probably be removed at a later stage.
    """
    def __init__(self, name=None, users=None):
        self.name = name
        self.users = users

    def to_json(self):
        """
        Method to turn an object into JSON.
        """
        return {'id': self.name, 'title': self.name, 'type': 'group'}

def authentication_dummy():
    """
    return the string 'user' and pretend authentication happened
    """
    return "user"


def localbox_path_decoder(path):
    """
    A 'localbox_path' is a unix filepath with the urlencoded components.
    """
    realpath = []
    components = path.split('/')
    for component in components:
        realpath.append(unquote(component))
    return '/'.join(realpath)


class LocalBoxHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    class extending the BaseHTTPRequestHandler and handling the HTTP requests
    in do_POST and do_GET (which in their turn forward said requests to
    do_request)
    """
    def exec_shares(self):
        """
        Handle share information
        """
        path2 = self.path.replace('/lox_api/shares/', '', 1)

        self.send_response(200)
        self.end_headers()

        data = list_share_items(path2)
        print data
        self.wfile.write(data)

    def exec_invitations(self):
        """
        Handle invitation listing
        """
        self.send_response(200)
        self.end_headers()
        self.wfile.write("invites")

    def exec_user(self):
        """
        Handle user info (or pretend to)
        """
        info = {'name': 'user', 'public_key': 'FT9CH-XVXW7',
                'private_key': 'RPR49-VDHYD', 'complete': 'No!'}
        self.wfile.write(dumps(info))

    def do_request(self):
        """
        Handle a request (do_POST and do_GET both forward to this function)
        """
        self.user = authentication_dummy()
        if not self.user:
            print "authentication problem"
            return
        for regex, function in ROUTING_LIST:
            print "Matching" + self.path + " with pattern " + regex.pattern
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
    httpd.serve_forever()
