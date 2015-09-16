"""
LocalBox shares module.
"""
from json import dumps
from .database import database_execute
from .encoding import LocalBoxJSONEncoder

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
