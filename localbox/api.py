"""
LocalBox API Implementation module. This module holds the implementation of the
API call handlers as well as directly related support functions
"""
from base64 import b64decode
from json import dumps
from json import loads
from logging import getLogger
from os import makedirs
from os import remove
from os import walk
from os.path import basename
from os.path import exists
from os.path import isdir
from os.path import isfile
from os.path import islink
from os.path import join
from os.path import lexists
from re import compile as regex_compile
from shutil import copyfile
from shutil import move
from shutil import rmtree

import localbox.utils
from localbox.utils import get_bindpoint

try:
    from urllib import unquote_plus  # pylint: disable=F0401,E0611
    from Cookie import SimpleCookie  # pylint: disable=F0401,E0611
except ImportError:
    from http.cookies import SimpleCookie  # pylint: disable=F0401,E0611
    from urllib.parse import unquote_plus  # pylint: disable=F0401,E0611

try:
    from os import symlink
except ImportError:
    # python26/windows fix for symlinking:
    # Origined from http://stackoverflow.com/questions/6260149/os-symlink-support-in-windows
    # As reported by Erik Renes, with minor changes
    def symlink(source, link_name):
        import os
        os_symlink = getattr(os, "symlink", None)
        if callable(os_symlink):
            os_symlink(source, link_name)
        else:
            import ctypes
            csl = ctypes.windll.kernel32.CreateSymbolicLinkW
            csl.argtypes = (
                ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
            csl.restype = ctypes.c_ubyte
            flags = 1 if os.path.isdir(source) else 0
            if csl(link_name, source, flags) == 0:
                raise ctypes.WinError()

from localbox.database import get_key_and_iv
from .database import database_execute
from localbox.files import get_filesystem_path
from localbox.files import get_key_path
from .files import stat_reader
from .files import SymlinkCache
from .shares import Share, ShareItem, Invitation
from .shares import list_share_items
from .shares import get_share_by_id
from .shares import get_database_invitations
from .encoding import localbox_path_decoder
from .shares import toggle_invite_state
from loxcommon.config import ConfigSingleton


def ready_cookie(request_handler):
    """
    Readies a PHP-like cookie - not to be part of the final codebase
    """
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

    :param string: string to be encoded.
    :param encoding: optional encoding in case it should not by UTF8 encoded.
    :returns: the string as a socket write prepared bytes type.
    """
    try:
        return bytes(string, encoding)
    except TypeError:
        return string


def get_body_json(request_handler):
    """
    Reads the request handlers bode and parses it as a JSON object.

    :param request_handler: the object which has the body to extract as json
    :returns: json-parsed version of the requests' body.
    """
    return loads(request_handler.old_body)


def exec_leave_share(request_handler):
    """
    Handle the leave_share call. Removes the share with the specified path for
    the current user. Returns 200 if succesful, 404 on failure. Called via the
    routing list.

    :param request_handler: object holding the path of the share to leave
    """
    pathstart = request_handler.path.replace('/lox_api/shares/', '', 1)
    path = pathstart.replace('/leave', '', 1)

    bindpoint = get_bindpoint()
    linkpath = join(bindpoint, request_handler.user, path)
    if islink(linkpath):
        remove(linkpath)
        request_handler.status = 200
    else:
        request_handler.status = 404


def exec_remove_shares(request_handler):
    """
    Removes a share from being shared. Everyones access to this share, except
    for that of the owner, is irrevokably removed by this call. Called via the
    routing list.

    :param request_handler: the object which contains the path to remove
    """
    share_start = request_handler.path.replace(
        '/lox_api/shares/', '', 1)
    shareid = int(share_start.replace('/revoke', '', 1))
    sql = 'remove from shares where id = ?'
    database_execute(sql, (shareid))
    request_handler.status = 200


def exec_edit_shares(request_handler):
    """
    Edits the list of people who can access a certain share object. A list of
    json encoded identities is in the body to represent the new list of people
    with access to said share. Called via the routing list

    :param request_handler: the object which contains the share id in its path
                           and list of users json-encoded in its body.
    """
    share_start = request_handler.path.replace(
        '/lox_api/shares/', '', 1)
    shareid = share_start.replace('/edit', '', 1)
    share = get_share_by_id(shareid)
    json = get_body_json(request_handler)
    symlinks = SymlinkCache()
    path = share.item.path
    links = symlinks.get(path)

    bindpoint = get_bindpoint()
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
    Handle share information for a path given in the request. Returns a list
    of shares containing the provided path. Called via the routing list.

    :param request_handler: the object with the path encoded in its path
    """
    path2 = request_handler.path.replace('/lox_api/shares/', '', 1)
    data = list_share_items(path2)
    request_handler.body = data
    request_handler.status = 200
    if data == "{}":
        request_handler.status = 404
        request_handler.body = None


def exec_invitations(request_handler):
    """
    Returns a list of all (pending) invitations for an user. Called via the
    routing list

    :param request_handler: object though which to return the values
    """
    request_handler.status = 200
    request_handler.body = get_database_invitations(
        request_handler.user)


def exec_invite_accept(request_handler):
    """
    Accepts/reopens an invitation to filesharing. called from the routing list.

    :param request_handler: the object containing invite identifier in its path
    """
    result = toggle_invite_state(request_handler, 'accepted')
    if result:
        request_handler.status = 200
    else:
        request_handler.status = 404


def exec_invite_reject(request_handler):
    """
    Rejects/cancels an invitation to filesharing. Called from the routing list

    :param request_handler: object with the invite identifier in its path
    """
    result = toggle_invite_state(request_handler, 'rejected')
    if result:
        request_handler.status = 200
    else:
        request_handler.status = 404


def exec_files_path(request_handler):
    """
    Allows for the up- and downloading of (encrypted) files to and from the
    localbox server. called from the routing list

    :param request_handler: the object which contains the files path in its path
    """
    path = request_handler.path.replace('/lox_api/files/', '', 1)
    if path != '':
        path = localbox_path_decoder(path)
    try:
        filepath = get_filesystem_path(path, request_handler.user)
    except ValueError as e:
        request_handler.status = 404
        request_handler.body = e.message
        return

    # getLogger(__name__).debug('body %s' % (request_handler.old_body),
    #                          extra=logging_utils.get_logging_extra(request_handler))

    contents = None
    if request_handler.old_body is not None:
        try:
            json_body = loads(request_handler.old_body)
            path = unquote_plus(json_body['path'])
            filepath = get_filesystem_path(path, request_handler.user)
            if json_body.has_key('contents'):
                contents = b64decode(json_body['contents'])
        except ValueError:
            contents = request_handler.old_body

    if request_handler.command == "POST" and contents is not None:
        request_handler.status = 200
        try:
            filedescriptor = open(filepath, 'wb')
            filedescriptor.write(contents)
        except IOError:
            getLogger('api').error('Could not write to file %s' % path,
                                   extra=localbox.utils.get_logging_extra(request_handler))
            request_handler.status = 500

    if request_handler.command == "GET" or (request_handler.command == "POST" and contents is None):
        if isdir(filepath):
            # Not really looping but we need the first set of values
            for path, directories, files in walk(filepath):
                if files is None or directories is None:
                    getLogger(__name__).info("filesystem related problems",
                                             extra=localbox.utils.get_logging_extra(request_handler))
                    return
                # path, directories, files = walk(filepath).next()
                dirdict = stat_reader(path, request_handler.user)
                dirdict['children'] = []
                for child in directories + files:
                    user = request_handler.user
                    childpath = join(filepath, child)
                    dirdict['children'].append(
                        stat_reader(childpath, user))
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
    Creates a new folder in the localbox directory structure. Called from the
    routing list

    :param request_handler: the object which has the path url-encoded in its
                           body
    """
    request_handler.status = 200
    path = unquote_plus(request_handler.old_body).replace("path=/", "", 1)
    getLogger(__name__).info("creating folder %s" % path, extra=localbox.utils.get_logging_extra(request_handler))
    bindpoint = get_bindpoint()
    filepath = join(bindpoint, request_handler.user, path)
    if lexists(filepath):
        getLogger(__name__).error("%s already exists" % path, extra=localbox.utils.get_logging_extra(request_handler))
        request_handler.status = 409  # Http conflict
        request_handler.body = "Error: Something already exits at path"
        return
    makedirs(filepath)
    getLogger('api').info("created directory " + filepath,
                          extra=request_handler.get_log_dict())
    request_handler.body = dumps(
        stat_reader(filepath, request_handler.user))


def exec_operations_delete(request_handler):
    """
    Removes a file or folder from the localbox directory structure. called from
    the routing list

    :param request_handler: the object which has the file path json-encoded in
                           its body
    """
    request_handler.status = 200
    user = request_handler.user
    pathstring = unquote_plus(
        request_handler.old_body).replace("path=/", "", 1)
    bindpoint = get_bindpoint()
    filepath = join(bindpoint, user, pathstring)

    getLogger(__name__).debug('deleting %s' % filepath,
                              extra=request_handler.get_log_dict())

    if not exists(filepath):
        request_handler.status = 404
        request_handler.body = "Error: No file exits at path"
        getLogger('api').error("failed to delete %s" % filepath,
                               extra=request_handler.get_log_dict())

        return
    if isdir(filepath):
        rmtree(filepath)
    else:
        remove(filepath)

    # remove keys
    sql = 'delete from keys where user = ? and path = ?'
    database_execute(sql, (user, get_key_path(user, localbox_path=pathstring)))

    SymlinkCache().remove(filepath)


def exec_operations_move(request_handler):
    """
    Moves a file within the localbox directory structure. Called from the
    routing list

    :param request_handler: the object which has the to_path and from_path
                           json-encoded in its body
    """
    json_object = loads(request_handler.old_body)
    bindpoint = get_bindpoint()
    move_from = join(
        bindpoint, request_handler.user, json_object['from_path'])
    move_to = join(
        bindpoint, request_handler.user, json_object['to_path'])
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
    copies a file within the localbox filesystem. Called from the routing list

    :param request_handler: object with to_path and from_path json-encoded in
                           its body
    """
    json_object = loads(request_handler.old_body)
    bindpoint = get_bindpoint()
    copy_from = join(
        bindpoint, request_handler.user, json_object['from_path'])
    copy_to = join(
        bindpoint, request_handler.user, json_object['to_path'])
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
    returns public- and private key information about the current user. Called
    from the routing list

    :param request_handler: object holding the user for which to return data
    """
    getLogger(__name__).info("running exec user", extra=request_handler.get_log_dict())
    if request_handler.command == "GET":
        sql = "select public_key, private_key from users where name = ?"
        result = database_execute(sql, (request_handler.user,))
        try:
            result_dictionary = {'user': request_handler.user, 'public_key': result[0][0],
                                 'private_key': result[0][1]}
        except IndexError:
            result_dictionary = {'user': request_handler.user}
        request_handler.body = dumps(result_dictionary)
    else:
        json_object = loads(request_handler.old_body)
        privkey = json_object['private_key']
        pubkey = json_object['public_key']
        sql = 'insert into users (public_key, private_key, name) values (?, ?, ?)'
        result = database_execute(
            sql, (pubkey, privkey, request_handler.user,))
        request_handler.body = dumps(
            {'name': request_handler.user, 'publib_key': pubkey, 'private_key': privkey})
    request_handler.status = 200


def exec_user_username(request_handler):
    """
    returns information about a certain user as specified in the url. Also
    return private key data if this is that user making the request

    :param request_handler: object containing the user for which to return data
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
    to a few database records to give the share an identifier.

    :param request_handler: object with the share filepath encoded in its path
    """
    body = request_handler.old_body
    json_list = loads(body)
    getLogger(__name__).debug('request data: %s' % json_list, extra=request_handler.get_log_dict())
    path2 = request_handler.path.replace(
        '/lox_api/share_create/', '', 1)
    bindpoint = get_bindpoint()
    sender = request_handler.user
    from_file = join(bindpoint, sender, path2)
    getLogger(__name__).debug('from_file: %s' % from_file, extra=request_handler.get_log_dict())
    # TODO: something something something group
    share = Share(sender, None, ShareItem(path=path2))
    share.save_to_database()
    request_handler.status = 200
    for json_object in json_list['identities']:
        if json_object['type'] == 'user':
            receiver = json_object['username']
            to_file = join(bindpoint, receiver, path2)
            getLogger(__name__).debug('to_file: %s' % to_file, extra=request_handler.get_log_dict())
            if exists(to_file):
                getLogger(__name__).error("destination " + to_file + " exists.", extra=request_handler.get_log_dict())
                request_handler.status = 500
                return
            if not exists(from_file):
                getLogger(__name__).error("source " + from_file + "does not exist.",
                                          extra=request_handler.get_log_dict())
                request_handler.status = 500
                return
            try:
                symlink(from_file, to_file)
            except OSError:
                getLogger('api').error("Error making symlink from " + from_file +
                                       " to " + to_file, extra=request_handler.get_log_dict())
                request_handler.status = 500
            invite = Invitation(
                None, 'pending', share, sender, receiver)
            invite.save_to_database()


def exec_key(request_handler):
    """
    returns rsa encrypted key and initialization vector for decoding the file
    in the specified path

    :param request_handler: object containing the file path encoded in its path
    """
    localbox_path = unquote_plus(request_handler.path.replace('/lox_api/key/', '', 1))
    while localbox_path.startswith('/'):
        localbox_path = localbox_path[1:]

    if request_handler.command == "GET":
        result = get_key_and_iv(localbox_path, request_handler.user)
        if result is not None:
            key, initvector = result  # pylint: disable=W0633
            request_handler.body = dumps({'key': key, 'iv': initvector})
            request_handler.status = 200
        else:
            request_handler.status = 404
    elif request_handler.command == "POST":
        data = request_handler.old_body
        # TODO: not crash on bull
        json_object = loads(data)
        sql = "insert into keys (path, user, key, iv) VALUES (?, ?, ?, ?)"
        database_execute(sql, (localbox_path, json_object['user'], json_object['key'],
                               json_object['iv']))
        request_handler.status = 200
        # TODO: recrypt encryped data


def exec_key_revoke(request_handler):
    """
    revoke/remove an encrypted key from the database so said user cannot access
    said key anymore.

    :param request_handler: object containing the path to the file in its path
                           and json encoded name of the user whoes key to
                           revoke
    """
    path = request_handler.path.replace('/lox_api/key_revoke/', '', 1)
    lengthstring = request_handler.headers.get('content-length')
    if lengthstring is None:
        user = request_handler.user
    else:
        data = request_handler.old_body
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

    :param request_handler: object with path encoded in its path
    """
    if (request_handler.path == '/lox_api/meta') or (request_handler.path == '/lox_api/meta/'):
        path = ''
    else:
        path = unquote_plus(
            request_handler.path.replace('/lox_api/meta/', '', 1))

    getLogger(__name__).debug('body %s' % (request_handler.old_body),
                              extra=localbox.utils.get_logging_extra(request_handler))
    if request_handler.old_body:
        path = unquote_plus(loads(request_handler.old_body)['path'])
        if path == '/':
            path = '.'

    try:
        try:
            filepath = get_filesystem_path(path, request_handler.user)
        except ValueError as e:
            request_handler.status = 404
            request_handler.body = e.message
            getLogger(__name__).error(e.message,
                                      extra=localbox.utils.get_logging_extra(request_handler))
            return
        result = stat_reader(filepath, request_handler.user)
        getLogger(__name__).debug('meta for filepath %s: %s' % (filepath, result),
                                  extra=localbox.utils.get_logging_extra(request_handler))
        if result is None:
            request_handler.status = 404
            request_handler.body = 'no meta found for %s. maybe the file does not exist' % filepath
            return
        result['children'] = []
        for path, directories, files in walk(filepath):
            for child in directories + files:
                user = request_handler.user
                childpath = join(filepath, child)
                result['children'].append(stat_reader(childpath, user))
            break
    except OSError as err:
        request_handler.status = 404
        getLogger(__name__).exception(err,
                                      extra=localbox.utils.get_logging_extra(request_handler))
    request_handler.body = dumps(result)
    request_handler.status = 200


def fake_login(request_handler):
    """
    part of the fake login process, not part of the final codebase

    :param request_handler: the object which has the body to extract as json
    """
    request_handler.new_headers = {"Date": "Mon, 26 Oct 2015 16:06:08 GMT",
                                   "Server": "Apache/2.4.16 (Fedora) OpenSSL/1.0.1k-fips PHP/5.6.14",
                                   "X-Powered-By": "PHP/5.6.14",
                                   "Set-Cookie": "PHPSESSID=ft41ihtl7uptocchfb1cj2ko95; expires=Tue, 27-Oct-2015 16:06:09 GMT; Max-Age=86400; path=/",
                                   "Cache-Control": "no-cache",
                                   "Access-Control-Allow-Origin": "*",
                                   "x-frame-options": "DENY",
                                   "Strict-Transport-Security": "max-age=86400",
                                   "Keep-Alive": "timeout=5, max=100",
                                   "Connection": "Keep-Alive",
                                   "Transfer-Encoding": "chunked",
                                   "Content-Type": "text/html; charset=UTF8"}
    form = """<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta charset="utf-8"/>
        <title>Sign in</title>

                                <link href="/localbox/web/bundles/rednoseframework/bootstrap/css/bootstrap.min.css" rel="stylesheet" />


    <link href="/localbox/web/bundles/rednoseframework/css/login.css" rel="stylesheet" />
    </head>
    <body>

    <div class="content">
      <h2>Sign in</h2>
        <form action="/login_check" method="POST">

        <input type="hidden" name="_csrf_token" value="482f45992b7cfec0ffac259f25bc981e70371aa3" />


          <div>
            <input id="username" name="_username" required="required" value="" autofocus="autofocus" type="text" placeholder="Username">
          </div>
          <div>
            <input id="password" name="_password" required="required" type="password" placeholder="Password">
          </div>
          <div>
              <label class="checkbox"><input type="checkbox" id="remember_me" name="_remember_me">Remember me</label>
          </div>
          <div class="footer">
                            <input class="btn btn-primary pull-right" type="submit" id="_submit" name="_submit" value="Sign in" />
          </div>
      </form>
    </div>

    </body>
</html>"""
    request_handler.status = 200
    request_handler.body = form


def fake_login_check(request_handler):
    """
    part of the fake login process, not part of the final codebase

    :param request_handler: the object which has the body to extract as json
    """
    url = request_handler.protocol + \
          request_handler.headers['Host'] + request_handler.path
    request_handler.new_headers = {"Date": "Mon, 26 Oct 2015 16:06:08 GMT",
                                   "Server": "Apache/2.4.16 (Fedora) OpenSSL/1.0.1k-fips PHP/5.6.14",
                                   "X-Powered-By": "PHP/5.6.14",
                                   "Set-Cookie": "PHPSESSID=rjcc3p0uila4qcu9btvf75ihd5; expires=Tue, 27-Oct-2015 16:06:30 GMT; Max-Age=86400; path=/",
                                   "Cache-Control": "no-cache",
                                   "Location": url + "/register_app",
                                   "Access-Control-Allow-Origin": "*",
                                   "x-frame-options": "DENY",
                                   "Strict-Transport-Security": "max-age=86400",
                                   "Keep-Alive": "timeout=5, max=100",
                                   "Connection": "Keep-Alive",
                                   "Transfer-Encoding": "chunked",
                                   "Content-Type": "text/html; charset=UTF8"}
    html = """<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8" />
        <meta http-equiv="refresh" content="1;url=""" + url + """/register_app" />

        <title>Redirecting to """ + url + """/register_app</title>
    </head>
    <body>
        Redirecting to <a href=\"""" + url + """ /register_app">http://192.168.178.25/localbox/web/app.php/register_app</a>.
    </body>
</html>"""
    # ready_cookie(request_handler)
    request_handler.status = 302
    request_handler.body = html


def fake_register_app(request_handler):
    """
    part of the fake login process, most definitely not part of the final
    codebase

    :param request_handler: the object which has the body to extract as json
    """
    configparser = ConfigSingleton('localbox')
    hostcrt = configparser.get('httpd', 'certfile')

    backurl = configparser.get('oauth', 'direct_back_url')
    y = open('host.crt').read()
    result = {'baseurl': backurl, 'name': 'schimmelpenning',
              'user': request_handler.user, 'logourl': 'http://8ch.net/static/logo_33.svg',
              'BackColor': '#00FF00', 'FontColor': '#0000FF', 'APIKeys':
                  [{'Name': 'LocalBox iOS', 'Key': 'keystring',
                    'Secret': 'secretstring'}],
              'pin_cert': ''.join(y.split('\n')[1:-2])
              }
    request_handler.status = 200
    request_handler.body = dumps(result)


def fake_oauth(request_handler):
    """
    part of the fake login process, not part of the final codebase

    :param request_handler: the object which has the body to extract as json

    NOTE: this was support for the localbox app and is now most likely depricated. Please remove as fast as possible
    """
    if "token" in request_handler.path:
        print(
            "============================================ FAKE OAUTH PART 3")
        request_handler.status = 200
        result = {"access_token": "2DHJlWJTui9d1pZnDDnkN6IV1p9Qq9",
                  "token_type": "Bearer", "expires_in": 600,
                  "refresh_token": "tNXAVVo2QE7c5MKgFCB1mKuAPsu4xL",
                  "scope": "all"}
        request_handler.body = result
    elif request_handler.command != "POST":
        print(
            "============================================ FAKE OAUTH PART 1")
        html = '<html><head></head><body><form action="/oauth2/v2/auth" ' \
               'method="POST"><input type="submit" value="allow"></form>' \
               '</body></html>'
        request_handler.status = 200
        request_handler.new_headers.append(
            ('Content-type', 'text/html',))
        request_handler.body = html
    else:
        print(
            "============================================ FAKE OAUTH PART 2")
        request_handler.status = 302
        request_handler.new_headers.append(('Location',
                                            'lbox://oauth-return?code=yay'))


def exec_identities(request_handler):
    """
    returns a list of all (known) users

    :param request_handler: object in which to return the userlist
    """
    sql = 'select name, not ((public_key == "" or public_key is NULL) and (private_key == "" or private_key is NULL)) as haskey from users;'
    result = database_execute(sql)
    outputlist = []
    for entry in result:
        outputlist.append({'id': entry[0], 'title': entry[0], 'username': entry[
            0], 'type': 'user', 'has_keys': bool(entry[1])})
    if outputlist == []:
        request_handler.status = 404
    else:
        request_handler.status = 200
        request_handler.body = dumps(outputlist)


def fake_set_cookies(request_handler):
    """
    not part of final codebase
    """
    request_handler.status = 404


# list with regex: function pairs. The regex is to be matched with the url
# requested. When the regex matches, the function is called with the
# request_handler as argument.
ROUTING_LIST = [
    (regex_compile(r"\/lox_api\/files.*"), exec_files_path),
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
    (regex_compile(r"\/lox_api\/meta.*"), exec_meta),
    (regex_compile(r"\/lox_api\/identities"), exec_identities),

    (regex_compile(r".*\/login"), fake_login),
    (regex_compile(r"\/login_check"), fake_login_check),
    (regex_compile(r"\/register_app"), fake_register_app),
    (regex_compile(r"\/oauth.*"), fake_oauth),
    (regex_compile(r"\/.*"), fake_set_cookies),
]
