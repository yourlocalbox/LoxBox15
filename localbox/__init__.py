"""
LocalBox main initialization class.
"""
from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from json import dumps, JSONEncoder
from re import compile as regex_compile
from ssl import wrap_socket
from urllib import unquote

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


class Invitation(object):
    """
    The state of being asked to join in sharing a file.
    """
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REVOKED = 'revoked'

    def __init__(self, identifier=None, state=None, share=None, sender=None,
                 receiver=None):
        self.identifier = identifier
        self.state = state
        self.share = share
        self.sender = sender
        self.receiver = receiver

    def to_json(self):
        """
        This creates a JSON serialisation of the Invitation. This serialisation
        is primarily for returning values and not a complete serialisation.
        """
        return {'id': self.identifier, 'share': self.share, 'item': self.share['item']}

class ShareItem(object):
    """
    Item that signifies a 'share'. Sharing a folder allows a different user to
    access yor file/folder. A ShareItem is the representation of that folder
    """
    def __init__(self, icon=None, path=None, has_keys=False, is_share=False,
                 is_shared=False, modified_at=None, title=None, is_dir=False):
        self.icon = icon
        self.path = path
        self.has_keys = has_keys
        self.is_share = is_share
        self.is_shared = is_shared
        self.modified_at = modified_at
        self.title = title
        self.is_dir = is_dir

    def to_json(self):
        """
        Create a JSON encoded string out of this ShareItem. This is used by the
        LocalBoxJSONEncoder to create JSON responses.
        """
        return {'icon': self.icon, 'path': self.path,
                'has_keys': self.has_keys,
                'is_share': self.is_share, 'is_shared': self.is_shared,
                'modified_at': self.modified_at, 'title': self.title,
                'is_dir': self.is_dir}


class Share(object):
    """
    THe state of sharing a folder.
    """
    def __init__(self, users=None, identifier=None, item=None):
        self.users = users
        self.identifier = identifier
        self.item = item

    def to_json(self):
        return {'identities': self.users, 'id': self.identifier,
                'item': self.item}


def list_share_items(path=None):
    """
    returns a list of ShareItems. If 'path' is given, only ShareItems for said
    path are returned.
    """
    if path is None:
        data = database_execute('select shareitem.icon, shareitem.path, ' +
                                'shareitem.has_keys, shareitem.is_share, ' +
                                'shareitem.is_shared, shareitem.modified_at, ' +
                                'shareitem.title, shareitem.is_dir, shares.id ' +
                                'from shareitem,' +
                                'shares where shares.path = shareitem.path')
    else:
        data = database_execute('select shareitem.icon, shareitem.path, ' +
                                'shareitem.has_keys, shareitem.is_share, ' +
                                'shareitem.is_shared, shareitem.modified_at, ' +
                                'shareitem.title, shareitem.is_dir, shares.id ' +
                                'from shareitem, shares where ' +
                                'shares.path = shareitem.path and ' +
                                'shareitem.path = ?', (path,))
    returndata = []
    for entry in data:
        shareid = entry[8]
        item = ShareItem(entry[0], entry[1], entry[2], entry[3], entry[4],
                         entry[5], entry[6], entry[7])
        users = []
        userentries = database_execute('select shares.user from shares where ' +
                                       'shares.id = ?', (shareid,))
        for userentry in userentries:
            users.append(User(userentry[0]))
        returndata.append(Share(users, shareid, item))
    return dumps(returndata, cls=LocalBoxJSONEncoder)


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

ROUTING_LIST = [
    (regex_compile(r"\/lox_api\/invitations"),
     LocalBoxHTTPRequestHandler.exec_invitations),
    (regex_compile(r"\/lox_api\/user"), LocalBoxHTTPRequestHandler.exec_user),
    (regex_compile(r"\/lox_api\/shares\/.*"), LocalBoxHTTPRequestHandler.exec_shares),
]


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
