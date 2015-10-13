"""
LocalBox API Implementation module. This module holds the implementation of the
API call handlers as well as directly related support functions
"""
from json import dumps
from json import loads
from re import compile as regex_compile
from os import remove
from os import symlink
from os import walk
from os import mkdir
from os.path import islink
from os.path import join
from os.path import exists
from os.path import lexists
from os.path import isfile
from os.path import isdir
from os.path import basename
from shutil import copyfile
from shutil import move
try:
    from Cookie import SimpleCookie  # pylintL disable=F0401
except ImportError:
    from http.cookies import SimpleCookie  # pylint: disable=F0401

from .database import get_key_and_iv
from .database import database_execute
from .files import get_filesystem_path
from .files import stat_reader
from .files import SymlinkCache
from .shares import Share, ShareItem, Invitation
from .shares import list_share_items
from .shares import get_share_by_id
from .shares import get_database_invitations
from .encoding import localbox_path_decoder
from .shares import toggle_invite_state
from .config import ConfigSingleton


def ready_cookie(request_handler):
    host = request_handler.headers.get('Host')
    cookie = SimpleCookie()
    cookie['PHPSESSID'] = "21345"
    cookie['PHPSESSID']['Domain'] = host
    cookie['PHPSESSID']['path'] = "/"
    cookie['PHPSESSID']['version'] = "1"
    request_handler.new_headers.append(('Set-Cookie',
                                        cookie.output(header=''),))


def prepare_string(string, encoding="UTF-8"):
    """
    Prepares a string to be sent over the wire. Python3 requires 'string's to
    be encoded as bytes accoding to an encoding (e.g. UTF8) before sending them
    through a socket. Within python2, 'bytes' more or less are strings, and the
    bytes' constructor only accepts one argument. Hence, this function will
    return the right type of object for sending over the network.
    @param string string to be encoded.
    @param encoding optional encoding in case it should not by UTF8 encoded.
    @return the string as a socket write prepared bytes type.
    """
    try:
        return bytes(string, encoding)
    except TypeError:
        return string


def get_body_json(request_handler):
    """
    Extracts a json element from the requests' body
    @param request_handler the object which has the body to extract as json
    @returns json-parsed version of the requests' body.
    """
    length = int(request_handler.headers.get('content-length', 0))
    value = request_handler.rfile.read(length)
    return loads(value)


def exec_leave_share(request_handler):
    """
    Handle the leave_share call. Removes the share with the specified path for
    the current user.
    @param request_handler the object which has the body to extract as json
    """
    pathstart = request_handler.path.replace('/lox_api/shares/', '', 1)
    path = pathstart.replace('/leave', '', 1)

    bindpoint = ConfigSingleton().get('filesystem', 'bindpoint')
    linkpath = join(bindpoint, request_handler.user, path)
    if islink(linkpath):
        remove(linkpath)
        request_handler.status = 200
    else:
        request_handler.status = 404


def exec_remove_shares(request_handler):
    """
    Removes a share from being shared. Everyones access to this share, except
    for that of the owner, is irrevokably removed by this call.
    @param request_handler the object which has the body to extract as json
    """
    share_start = request_handler.path.replace('/lox_api/shares/', '', 1)
    shareid = int(share_start.replace('/revoke', '', 1))
    sql = 'remove from shares where id = ?'
    database_execute(sql, (shareid))
    request_handler.status = 200


def exec_edit_shares(request_handler):
    """
    Edits the list of people who can access a certain share object. A list of
    json encoded identities is in the body to represent the new list of people
    with access to said share.
    @param request_handler the object which has the body to extract as json
    """
    share_start = request_handler.path.replace('/lox_api/shares/', '', 1)
    shareid = share_start.replace('/edit', '', 1)
    share = get_share_by_id(shareid)
    json = get_body_json(request_handler)
    symlinks = SymlinkCache()
    path = share.item.path
    links = symlinks.get(path)

    bindpoint = ConfigSingleton().get('filesystem', 'bindpoint')
    newlinks = []
    for entry in json:
        to_file = join(bindpoint, entry.title, basename(entry.path))
        newlinks.append(to_file)
        symlink(path, to_file)
    for link in links:
        if link not in newlinks:
            remove(link)
            symlinks.remove(link)


def exec_shares(request_handler):
    """
    Handle share information for a path given in the request
    @param request_handler the object which has the body to extract as json
    """
    path2 = request_handler.path.replace('/lox_api/shares/', '', 1)
    data = list_share_items(path2)
    request_handler.body = data
    request_handler.status = 200


def exec_invitations(request_handler):
    """
    Returns a list of all (pending) invitations
    @param request_handler the object which has the body to extract as json
    """
    request_handler.status = 200
    request_handler.body = get_database_invitations(request_handler.user)


def exec_invite_accept(request_handler):
    """
    Accepts/reopens an invitation to filesharing.
    @param request_handler the object which has the body to extract as json
    """
    result = toggle_invite_state(request_handler, 'accepted')
    if result:
        request_handler.status = 200
    else:
        request_handler.status = 404


def exec_invite_reject(request_handler):
    """
    Rejects/cancels an invitation to filesharing.
    @param request_handler the object which has the body to extract as json
    """
    result = toggle_invite_state(request_handler, 'rejected')
    if result:
        request_handler.status = 200
    else:
        request_handler.status = 404


def exec_files_path(request_handler):
    """
    Allows for the up- and downloading of (encrypted) files to and from the
    localbox server.
    @param request_handler the object which has the body to extract as json
    """
    path = request_handler.path.replace('/lox_api/files/', '', 1)
    if path != '':
        path = localbox_path_decoder(path)
    filepath = get_filesystem_path(path, request_handler.user)
    if request_handler.command == "POST":
        filedescriptor = open(filepath, 'wb')
        length = int(request_handler.headers.get('content-length'))
        filedescriptor.write(request_handler.rfile.read(length))

    if request_handler.command == "GET":
        if isdir(filepath):
            # Not really looping but we need the first set of values
            for path, directories, files in walk(filepath):
                if files is None or directories is None:
                    print("filesystem related problems")
                    return
                # path, directories, files = walk(filepath).next()
                dirdict = stat_reader(path, request_handler.user)
                dirdict['children'] = []
                for child in directories + files:
                    user = request_handler.user
                    childpath = join(filepath, child)
                    dirdict['children'].append(stat_reader(childpath, user))
                request_handler.body = dumps(dirdict)
                break
        elif exists(filepath):
            filedescriptor = open(filepath, 'rb')
            request_handler.body = filedescriptor.read()
            request_handler.status = 200
        else:
            request_handler.status = 404


def exec_operations_create_folder(request_handler):
    """
    Creates a new folder in the localbox directory structure
    @param request_handler the object which has the body to extract as json
    """
    length = int(request_handler.headers.get('content-length'))
    json_object = loads(request_handler.rfile.read(length))
    bindpoint = ConfigSingleton().get('filesystem', 'bindpoint')
    filepath = join(bindpoint, request_handler.user, json_object['path'])
    if lexists(filepath):
        request_handler.status = 404
        request_handler.body = "Error: Something already exits at path"
        return
    mkdir(filepath)


def exec_operations_delete(request_handler):
    """
    removes a file or folder from the localbox directory structure
    @param request_handler the object which has the body to extract as json
    """
    length = int(request_handler.headers.get('content-length'))
    json_object = loads(request_handler.rfile.read(length))
    bindpoint = ConfigSingleton().get('filesystem', 'bindpoint')
    filepath = join(bindpoint, request_handler.user, json_object['path'])
    if not exists(filepath):
        request_handler.status = 404
        request_handler.body = "Error: No file exits at path"
        return
    remove(filepath)
    SymlinkCache().remove(filepath)


def exec_operations_move(request_handler):
    """
    moves a file within the localbox directory structure
    @param request_handler the object which has the body to extract as json
    """
    length = int(request_handler.headers.get('content-length'))
    json_object = loads(request_handler.rfile.read(length))
    bindpoint = ConfigSingleton().get('filesystem', 'bindpoint')
    move_from = join(bindpoint, request_handler.user, json_object['from_path'])
    move_to = join(bindpoint, request_handler.user, json_object['to_path'])
    if not isfile(move_from):
        request_handler.status = 404
        request_handler.body = "Error: No file exits at from_path"
        return
    if lexists(move_to):
        request_handler.status = 404
        request_handler.body = "Error: A file already exists at to_path"
        return
    move(move_from, move_to)


def exec_operations_copy(request_handler):
    """
    copies a file within the localbox filesystem
    @param request_handler the object which has the body to extract as json
    """
    length = int(request_handler.headers.get('content-length'))
    json_object = loads(request_handler.rfile.read(length))
    bindpoint = ConfigSingleton().get('filesystem', 'bindpoint')
    copy_from = join(bindpoint, request_handler.user, json_object['from_path'])
    copy_to = join(bindpoint, request_handler.user, json_object['to_path'])
    if not exists(copy_from):
        request_handler.status = 404
        request_handler.body = "Error: No file exits at from_path"
        return
    if lexists(copy_to):
        request_handler.status = 404
        request_handler.body = "Error: A file already exists at to_path"
        return
    copyfile(copy_from, copy_to)

    request_handler.status = 200


def exec_user(request_handler):
    """
    returns public- and private key information about the current user
    @param request_handler the object which has the body to extract as json
    """
    print("running exec user")
    sql = "select public_key, private_key from users where name = ?"
    result = database_execute(sql, (request_handler.user,))[0]
    result_dictionary = {'user': request_handler.user, 'public_key': result[0],
                         'private_key': result[1]}
    request_handler.body = dumps(result_dictionary)


def exec_user_username(request_handler):
    """
    returns information about a certain user as specified in the url. Also
    return private key data if this is that user making the request
    @param request_handler the object which has the body to extract as json
    """
    username = request_handler.path.replace('/lox_api/user/', '', 1)
    if username == request_handler.user:
        sql = 'select public_key, private_key from users where name = ?;'
    else:
        sql = 'select public_key from users where name = ?;'

    result = database_execute(sql, (username,))
    if result == []:
        request_handler.status = 404
        request_handler.body = "Unknown user"
        return
    else:
        request_handler.status = 200

    info = {'name': username, 'public_key': result[0]}
    if username == request_handler.user:
        info['private_key'] = result[1]
    request_handler.body = dumps(info)


def exec_create_share(request_handler):
    """
    Creates a 'share' within localbox. Comes down to creating a symlink next
    to a few database records to give the share an identifier
    @param request_handler the object which has the body to extract as json
    """
    length = int(request_handler.headers.get('content-length'))
    body = request_handler.rfile.read(length)
    json_list = loads(body)
    path2 = request_handler.path.replace('/lox_api/share_create/', '', 1)
    bindpoint = ConfigSingleton().get('filesystem', 'bindpoint')
    sender = request_handler.user
    from_file = join(bindpoint, sender, path2)
    # TODO: something something something group
    share = Share(sender, None, ShareItem(path=path2))
    share.save_to_database()
    for json_object in json_list:
        if json_object['type'] == 'user':
            receiver = json_object['username']
            to_file = join(bindpoint, receiver, path2)
            if exists(to_file):
                print("destination " + to_file + " exists.")
                request_handler.status = 500
                return
            if not exists(from_file):
                print("source " + from_file + "does not exist.")
                request_handler.status = 500
                return
            symlink(from_file, to_file)
            invite = Invitation(None, 'pending', share, sender, receiver)
            invite.save_to_database()
    request_handler.status = 200


def exec_key(request_handler):
    """
    returns rsa encrypted key and initialization vector for decoding the file
    in the specified path
    @param request_handler the object which has the body to extract as json
    """
    localbox_path = request_handler.path.replace('/lox_api/key/', '', 1)
    if request_handler.command == "GET":
        key, initvector = get_key_and_iv(localbox_path, request_handler.user)
        request_handler.body = dumps({'key': key, 'iv': initvector})
    elif request_handler.command == "POST":
        length = int(request_handler.headers.get('content-length'))
        data = request_handler.rfile.read(length)
        json_object = loads(data)
        sql = "insert into keys (path, user, key, iv) VALUES (?, ?, ?)"
        database_execute(sql, (localbox_path, json_object['key'],
                               json_object['iv']))


def exec_key_revoke(request_handler):
    """
    revoke/remove an encrypted key from the database so said user cannot access
    said key anymore.
    @param request_handler the object which has the body to extract as json
    """
    path = request_handler.path.replace('/lox_api/key_revoke/', '', 1)
    lengthstring = request_handler.headers.get('content-length')
    if lengthstring is None:
        user = request_handler.user
    else:
        data = request_handler.rfile.read(int(lengthstring))
        user = loads(data)['username']
        # Let's either not allow users to add a username or not have the
        # restriction that they cannot get the data back next time
        if user != request_handler.user:
            request_handler.status = 403
    sql = 'remove from keys where user = ? and path = ?;'
    database_execute(sql, (user, path))


def exec_meta(request_handler):
    """
    returns metadata for a given file/directory
    @param request_handler the object which has the body to extract as json
    """
    path = request_handler.path.replace('/lox_api/meta/', '', 1)
    result = stat_reader(get_filesystem_path(path, request_handler.user),
                         request_handler.user)
    request_handler.body = dumps(result)
    request_handler.status = 200


def fake_login(request_handler):
    """
    part of the fake login process
    @param request_handler the object which has the body to extract as json
    """
    form = '<form action="login_check" method="POST">'\
           '<input type="submit" value="signin"> </form>'
    request_handler.body = form
    request_handler.status = 200


def fake_login_check(request_handler):
    """
    part of the fake login process
    @param request_handler the object which has the body to extract as json
    """
    html = '<meta http-equiv="refresh" content="1,url=/register_app />'\
           '<a href="/register_app">next</a>'
    request_handler.send_header('Location', '/register_app')
    ready_cookie(request_handler)
    request_handler.status = 302
    request_handler.body = html


def fake_register_app(request_handler):
    """
    part of the fake login process
    @param request_handler the object which has the body to extract as json
    """
    result = {'baseurl': 'https://localhost:8000/', 'name': 'schimmelpenning',
              'user': 'user', 'logourl': 'https://8ch.net/static/logo_33.svg',
              'BackColor': '#0000FF', 'FontColor': '#FF0000', 'APIKeys':
              [{'Name': 'LocalBox iOS', 'Key': 'keystring',
                'Secret': 'secretstring'}],
              'pin_cert': 'MIIDVzCCAj+gAwIBAgIJAKn6Bcf2mTH+MA0GCSqGSIb3DQEBCwU'
                          'AMEIxCzAJBgNVBAYTAlhYMRUwEwYDVQQHDAxEZWZhdWx0IENpdH'
                          'kxHDAaBgNVBAoME0RlZmF1bHQgQ29tcGFueSBMdGQwHhcNMTUwO'
                          'TE1MTAyODM3WhcNMTYwOTE0MTAyODM3WjBCMQswCQYDVQQGEwJY'
                          'WDEVMBMGA1UEBwwMRGVmYXVsdCBDaXR5MRwwGgYDVQQKDBNEZWZ'
                          'hdWx0IENvbXBhbnkgTHRkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ'
                          '8AMIIBCgKCAQEAuhdfwhBc0pIaRxeq4+xv6WZVIb0PSbW8G6kJ7'
                          'kbw+NL0s+FS+Au0JQNtOqauiYdi09ejqfHHUW+cLoX3qMeH2Wgr'
                          '9TuIbRamLOJw/twstq0LqKOjaiLgq/xRNcUrqptgDfXSbBQXRcG'
                          'sdB+6E6pKGfViDIZzhdgImXKqROfa6Yv5aGHuz204sKovu2/gSH'
                          'Pz2IDXSdAehpNbJ5ORFP3+Gkb1z6VoZvJ5QAp/+Ri3th8ms6o/D'
                          'XRhwSCtetKQshyRjYXpea3v/Oq9lbzBm43LhzyH24ThwKKX8p1J'
                          'tCJcMfHzpa9OHgLNpDDp4AKCcq5KcDRWJxoTDs45Noj/j3PtlQI'
                          'DAQABo1AwTjAdBgNVHQ4EFgQUibXrIXzSfhlh/ndNG4cMjIHg3v'
                          '8wHwYDVR0jBBgwFoAUibXrIXzSfhlh/ndNG4cMjIHg3v8wDAYDV'
                          'R0TBAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAQEALEzFqDhRgiRW'
                          'xJJx3CwG41VadNYJxxgvVos0sVc4y7fTWG2Rq42mMVbMGBvqxtz'
                          '69KwcHGAvfC1DteEdTSHmEuhsR4DiX0mChfNQrWvrbDTnKaa00a'
                          'aWArVMUGa+vbDFxsW+r0Z+hzBneQI9Qiy8dexUD3etV7EIumijE'
                          'faPDvMDNnwwVGj17D7EXY/aDgFQqwTiPGlzOE73kcFTzkMMRzkN'
                          'hurcNbhp/Z92ToL92LgetAVIrMNysWrgCJrI/gh7nPZIX6LH5TD'
                          '0Erlx/NEP5IKcsVUnIxH+aXQD4sHjreiUxdPpuqsAy3u4ThMI+o'
                          '5Rj6Iq1M5L8sPjJ6WzkEXblw==',
              "access_token": "2DHJlWJTui9d1pZnDDnkN6IV1p9Qq9",
              "token_type": "Bearer", "expires_in": 600,
              "refresh_token": "tNXAVVo2QE7c5MKgFB1mKuAPsu4xL", "scope": "all"}
    request_handler.status = 200
    request_handler.body = dumps(result)


def fake_oauth(request_handler):
    """
    part of the fake login process
    @param request_handler the object which has the body to extract as json
    """
    if request_handler.command != "POST":
        html = '<html><head></head><body><form action="/oauth2/v2/auth" '\
               'method="POST"><input type="submit" value="allow"></form>'\
               '</body></html>'
        request_handler.status = 200
        request_handler.new_headers.append(('Content-type', 'text/html',))
        request_handler.body = html
    else:
        request_handler.status = 302
        request_handler.new_headers.append('Location',
                                           'lbox://oauth-return?code=xkcd')
        result = {"access_token": "2DHJlWJTui9d1pZnDDnkN6IV1p9Qq9",
                  "token_type": "Bearer", "expires_in": 600,
                  "refresh_token": "tNXAVVo2QE7c5MKgFCB1mKuAPsu4xL",
                  "scope": "all"}
        request_handler.body = result


def exec_identities(request_handler):
    """
    returns a list of all users
    @param request_handler the object which has the body to extract as json
    """
    sql = 'select name from users;'
    result = database_execute(sql)
    outputlist = []
    for entry in result:
        outputlist.append({'id': entry[0], 'name': entry[0], 'type': 'user'})
    request_handler.body = dumps(outputlist)


def fake_set_cookies(request_handler):
    request_handler.status = 404

ROUTING_LIST = [
    (regex_compile(r"\/lox_api\/files\/.*"), exec_files_path),
    (regex_compile(r"\/lox_api\/invitations"), exec_invitations),
    (regex_compile(r"\/lox_api\/invite/[0-9]+/accept"), exec_invite_accept),
    (regex_compile(r"\/lox_api\/invite/[0-9]+/revoke"), exec_invite_reject),
    (regex_compile(r"\/lox_api\/operations\/copy"), exec_operations_copy),
    (regex_compile(r"\/lox_api\/operations\/move"), exec_operations_move),
    (regex_compile(r"\/lox_api\/operations\/delete"), exec_operations_delete),
    (regex_compile(r"\/lox_api\/operations\/create_folder"),
     exec_operations_create_folder),
    (regex_compile(r"\/lox_api\/share_create\/.*"), exec_create_share),
    (regex_compile(r"\/lox_api\/shares\/.*\/edit"), exec_edit_shares),
    (regex_compile(r"\/lox_api\/shares\/.*\/revoke"), exec_remove_shares),
    (regex_compile(r"\/lox_api\/shares\/.*\/leave"), exec_leave_share),
    (regex_compile(r"\/lox_api\/shares\/.*"), exec_shares),
    (regex_compile(r"\/lox_api\/user\/.*"), exec_user_username),
    (regex_compile(r"\/lox_api\/user"), exec_user),
    (regex_compile(r"\/lox_api\/key\/.*"), exec_key),
    (regex_compile(r"\/lox_api\/key_revoke\/.*"), exec_key_revoke),
    (regex_compile(r"\/lox_api\/meta\/.*"), exec_meta),
    (regex_compile(r"\/lox_api\/identities"), exec_identities),

    (regex_compile(r"\/login"), fake_login),
    (regex_compile(r"\/login_check"), fake_login_check),
    (regex_compile(r"\/register_app"), fake_register_app),
    (regex_compile(r"\/oauth.*"), fake_oauth),
    (regex_compile(r"\/.*"), fake_set_cookies),
]
