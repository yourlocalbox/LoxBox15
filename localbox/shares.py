"""
LocalBox shares module.
"""
from os.path import join
from json import dumps
from localbox.utils import get_bindpoint
from logging import getLogger

from localbox import get_bindpoint
from .files import SymlinkCache
from .database import database_execute
from .encoding import LocalBoxJSONEncoder
from .files import stat_reader
from .files import get_filesystem_path
from .config import ConfigSingleton


class User(object):

    """
    User object, limited to more or less the 'name' only, given how the actual
    user administration is done by the authentication mechanism.
    """

    def __init__(self, name=None):
        self.name = name

    def to_json(self):
        """
        Method to turn this object into JSON.
        @return JSON representation of this User
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
        Method to turn this object into JSON.
        @return JSON representation of this Group
        """
        return {'id': self.name, 'title': self.name, 'type': 'group'}


class Invitation(object):

    """
    The state of being asked to join in sharing a file.
    """

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
        @return json representing this Invitation
        """
        # TODO: Add dates in database
        return {'id': self.identifier, 'share': self.share,
                'item': self.share.item, 'state': self.state, 'created_at': '2915-09-11T15:31:27+0200'}

    def save_to_database(self):
        """
        Saves the Invitation to the database
        """
        params = (self.sender, self.receiver, self.share.identifier,
                  self.state)
        if self.identifier is None:
            sql = "insert into invitations (sender, receiver, share_id, "\
                  "state) values (?, ?, ?, ?)"
        else:
            params = params + (self.identifier,)
            sql = "update invitations set sender = ?, receiver = ?, "\
                  "share_id = ?, state = ? where id = ?"

        database_execute(sql, params)
        if self.identifier is None:
            sql = "select id from invitations where sender = ? and " \
                  "receiver = ?  and share_id = ? and state = ?"
            result = database_execute(sql, params)
            self.identifier = result


def get_database_invitations(user):
    """
    returns all (relevant) invitations from the database for a specific user
    @param user the user for who to return invitations
    @return the invitations for this user
    """
    sql = "select id, sender, receiver, share_id, state from invitations " \
          "where receiver = ? and state != 'accepted'"
    result = database_execute(sql, (user,))
    invitation_list = []
    for entry in result:
        share = get_share_by_id(entry[3])
        invitation_list.append(Invitation(entry[0], entry[4], share, entry[1],
                                          entry[2]))
    return dumps(invitation_list, cls=LocalBoxJSONEncoder)


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
        @return JSON representation of the ShareItem
        """
        return {'icon': self.icon, 'path': self.path,
                'has_keys': self.has_keys,
                'is_share': self.is_share, 'is_shared': self.is_shared,
                'modified_at': self.modified_at, 'title': self.title,
                'is_dir': self.is_dir}


def get_shareitem_by_path(localbox_path, user):
    """
    returns a ShareItem as defined by the given path.
    @param localbox_path localbox specific filepath
    @param user name of the user for who to do this
    @return the metadata for the share on the supplied path
    """
    return stat_reader(get_filesystem_path(localbox_path, user), user)


class Share(object):

    """
    THe state of sharing a folder.
    """

    def __init__(self, users=None, identifier=None, item=None):
        self.users = users
        self.identifier = identifier
        self.item = item

    def add_user(self, user):
        """
        Adds a user to the Share object
        @param user the user to add
        """
        if self.users is not None:
            self.users.append(user)
        else:
            self.users = [user]

    def get_identities_json(self):
        result = "["
        for user in self.users:
            result = result + \
                dumps({'id': user, 'title': user, 'type': 'user'})
        result = result + "]"

    def to_json(self):
        """
        returns a json representation of this Share
        @return a json representation of this Share
        """
        return {'identities': self.get_identities_json(), 'id': self.identifier,
                'item': self.item}

    def save_to_database(self):
        """
        saves the current share to the database, either updating record 'id',
        or creating a new one if this Share has no ID yet.
        """
        params = (self.users, self.item.path)
        if self.identifier is None:
            sql = 'insert into shares (user, path) values (?, ?)'
        else:
            sql = 'update shares set user = ?, path = ? where id = ?'
            params = params + (self.identifier,)
        database_execute(sql, params)

        if self.identifier is None:
            sql = 'select id from shares where user = ? and path = ?'
            self.identifier = database_execute(sql, params)[0][0]


def get_share_by_id(identifier):
    """
    returns the share with the supplied identifier
    @param identifier the number identifying the share in question
    @return the Share identified by the identifier
    """
    sharesql = 'select user, path from shares where id = ?'
    packedsharedata = database_execute(sharesql, (identifier,))
    if packedsharedata == []:
        return None
    sharedata = packedsharedata[0]
    # itemsql = 'select icon, path, has_keys, is_share, is_shared, modified_at,'\
    #          'title, is_dir from shareitem where path = ?'

    # itemdata = database_execte(itemsql, (sharedata[1],))
    bindpoint = get_bindpoint()
    shareitem = stat_reader(
        join(bindpoint, sharedata[0], sharedata[1]), sharedata[1])

    # shareitem = ShareItem(itemdata[0], itemdata[1], itemdata[2], itemdata[3],
    # itemdata[4], itemdata[5], itemdata[6], itemdata[7])
    return Share(sharedata[0], identifier, shareitem)


def list_share_items(path=None, user=None):
    """
    returns a list of ShareItems. If 'path' is given, only ShareItems for said
    path are returned.
    @param path a path for which to return the ShareItems
    @return list of shareitems
    """
    results = []
    symlinks = SymlinkCache()
    getLogger(__name__).debug('get share items for path: %s' % path, extra={'user': None, 'ip': None, 'path': None})
    if path is not None:
        filesystem_path = join(get_bindpoint(), user, path)
        if symlinks.exists(filesystem_path):
            results = symlinks.get(filesystem_path)
    else:
        for value in symlinks.cache.values():
            results = results + value

    returndata = {}
    for entry in results:
        sql = "SELECT shares.id, shares.user from shares where shares.path = ?"
        shareinfo = database_execute(sql, (path,))[0]
        shareitem = get_shareitem_by_path(path, shareinfo[1])
        print shareitem
        if entry in returndata:
            returndata[entry].adduser(shareinfo[1])
        else:
            returndata[entry] = Share(
                shareinfo[1], shareinfo[0], shareitem)
    return dumps(returndata, cls=LocalBoxJSONEncoder)


def toggle_invite_state(request_handler, newstate):
    """
    sets the state of an invite to newstate.
    @param request_handler the request_handler with all required information to
                           extract the invite from.
    @param newstate the new state for the invite
    """
    invite_identifier = int(request_handler.path.split('/')[3])
    user = request_handler.user
    readsql = "select 1 from invitations where state!=? and receiver = ? and "\
              "id = ?"
    readresult = database_execute(
        readsql, (newstate, user, invite_identifier))
    if len(readresult) != 0:
        sql = "update invitations set state=? where receiver = ? and id = ?;"
        database_execute(sql, (newstate, user, invite_identifier))
        request_handler.status = 200
    return len(readresult) != 0
