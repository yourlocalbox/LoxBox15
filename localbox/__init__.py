from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from json import dumps, JSONEncoder
from re import compile
from ssl import wrap_socket
from urllib import unquote

from config import ConfigSingleton
from database import database_execute

from pprint import pprint


class MyEncoder(JSONEncoder):
    def default(self, o):
        if hasattr(o, 'to_JSON'):
            return o.to_JSON()
        return o.__dict__


class User(object):
    def __init__(self, name=None):
        self.name = name

    def to_JSON(self):
        return {'id': self.name, 'title': self.name, 'type': 'user'}


class Group(object):
    def __init__(self, name=None, users=[]):
        self.name = name
        self.users = users

    def to_JSON(self):
        return {'id': self.name, 'title': self.name, 'type': 'group'}


class Invitation(object):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REVOKED = 'revoked'

    def __init__(self, identifier=None, state=None, share=None, sender=None, receiver=None):
        self.identifier = identifier
        self.state = state
        self.share = share
        self.sender = sender
        self.receiver = receiver

    def to_JSON(self):
        """
        This creates a JSON serialisation of the Invitation. This serialisation is primarily for returning values and not a complete serialisation.
        """
        return {'id': identifier, 'share': share, 'item': share['item']
        }

class ShareItem(object):
    """
    Item that signifies a 'share'. Sharing a folder allows a different user to
    access yor file/folder. A ShareItem is the representation of that folder
    """
    def __init__(self, icon=None, path=None, has_keys=False, is_share=False,
                 is_shared=False, modified_at=None, title=None, is_dir=False):
        """
        Initialise the ShareItem
        """
        self.icon = icon
        self.path = path
        self.has_keys = has_keys
        self.is_share = is_share
        self.is_shared = is_shared
        self.modified_at = modified_at
        self.title = title
        self.is_dir = is_dir

    def to_JSON(self):
        """
        Create a JSON encoded string out of this ShareItem. This is used by the
        MyEncoder to create JSON responses.
        """
        return {'icon': self.icon, 'path': self.path,
                'has_keys': self.has_keys,
                'is_share': self.is_share, 'is_shared': self.is_shared,
                'modified_at': self.modified_at, 'title': self.title,
                'is_dir': self.is_dir}


class Share(object):
    def __init__(self, users=None, identifier=None, item=None):
        self.users = users
        self.identifier = identifier
        self.item = item

    def to_JSON(self):
        return {'identities': self.users, 'id': self.identifier, 'item': self.item}
    

def ListShareItems(path=None):
    """
    returns a list of ShareItems. If 'path' is given, only ShareItems for said path are returned.
    """
    if path is None:
        data = database_execute('select shareitem.icon, shareitem.path, shareitem.has_keys, shareitem.is_share, shareitem.is_shared, shareitem.modified_at, shareitem.title, shareitem.is_dir, shares.id from shareitem, shares where shares.path = shareitem.path')
    else:
        data = database_execute('select shareitem.icon, shareitem.path, shareitem.has_keys, shareitem.is_share, shareitem.is_shared, shareitem.modified_at, shareitem.title, shareitem.is_dir, shares.id from shareitem, shares where shares.path = shareitem.path and shareitem.path = ?', (path,))
    returndata = []
    for entry in data:
        shareid = entry[8]
        item = ShareItem(entry[0],entry[1], entry[2], entry[3], entry[4], entry[5], entry[6], entry[7])
        users = []
        userentries = database_execute('select shares.user from shares where shares.id = ?', (shareid,))
        for userentry in userentries:
            users.append(User(userentry[0]))
        returndata.append(Share(users, shareid, item))
    return dumps(returndata, cls=MyEncoder)
       


def AuthenticationDummy():
    return "user"


def LocalboxPathDecoder(path):
    realpath = ""
    components = path.split('/')
    for component in components:
        realpath = realpath + unquote(component)
    return realpath
    

class LocalBoxHTTPRequestHandler(BaseHTTPRequestHandler):
    def exec_shares(self):
        path2 = self.path.replace('/lox_api/shares/', '', 1)

        self.send_response(200)
        self.end_headers()

        data = ListShareItems(path2)
        print data
        self.wfile.write(data)

    def exec_invitations(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("invites")

    def exec_user(self):
        info = {'name': 'user', 'public_key': 'FT9CH-XVXW7',
                'private_key': 'RPR49-VDHYD', 'complete': 'No!'}
        self.wfile.write(dumps(info))

    def do_REQUEST(self):
        self.user = AuthenticationDummy()
        if not self.user:
            print "authentication problem"
            return
        for regex, function in RoutingList:
            print "Matching" + self.path + " with pattern " + regex.pattern
            if regex.match(self.path):
                function(self)

    def do_POST(self):
        print "do_POST"
        self.do_REQUEST()

    def do_GET(self):
        print "do_GET"
        self.do_REQUEST()

RoutingList = [
    (compile(r"\/lox_api\/invitations"),
     LocalBoxHTTPRequestHandler.exec_invitations),
    (compile(r"\/lox_api\/user"), LocalBoxHTTPRequestHandler.exec_user),
    (compile(r"\/lox_api\/shares\/.*"), LocalBoxHTTPRequestHandler.exec_shares),
]


def main():
    configparser = ConfigSingleton()
    certfile = configparser.get('httpd', 'certfile')
    keyfile = configparser.get('httpd', 'keyfile')
    port = int(configparser.get('httpd', 'port'))
    server_address = ('', port)
    httpd = HTTPServer(server_address, LocalBoxHTTPRequestHandler)
    httpd.socket = wrap_socket(httpd.socket, server_side=True,
                               certfile=certfile, keyfile=keyfile)
    httpd.serve_forever()
