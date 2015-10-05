"""
LocalBox API Implementation module
"""
from json import dumps
from json import loads
from re import compile as regex_compile
from os import remove
from os import symlink
from os import walk
from os import mkdir
from os import stat
from os.path import split
from os.path import join
from os.path import exists
from os.path import lexists
from os.path import isfile
from os.path import isdir
from os.path import basename
from shutil import copyfile
from shutil import move

from .database import database_execute
from .files import get_filesystem_path
from .files import stat_reader
from .files import SymlinkCache
from .shares import Share, ShareItem, Invitation
from .shares import list_share_items
from .shares import get_database_invitations
from .encoding import localbox_path_decoder
from .shares import toggle_invite_state
from .config import ConfigSingleton

def prepare_string(string, encoding="UTF-8"):
    """
    Prepares a string to be sent over the wire. Python3 requires 'string's to
    be encoded as bytes accoding to an encoding (e.g. UTF-8) before sending them
    through a socket. Within python2, 'bytes' more or less are strings, and the
    bytes' constructor only accepts one argument. Hence, this function will
    return the right type of object for sending over the network.
    @param string string to be encoded.
    @param encoding optional encoding in case it should not by UTF8 encoded.
    @return the string as a socket write prepared bytes type.
    """
    try:
        return(bytes(string, encoding))
    except TypeError:
        return string


def get_body_json(request_handler):
    """
    does the necesary things in order to extract a json element from the requests' body
    """
    length = int(request_handler.headers.get('content-length', 0))
    value = request_handler.rfile.read(length)
    return loads(value)


def exec_leave_share(request_handler):
    path = request_handler.path.replace('/lox_api/shares/', '', 1).replace('/leave', '',1)
    bindpoint = ConfigSingleton().get('filesystem', 'bindpoint')
    linkpath = join(bindpoint, request_handler.user, path)
    if(islink(linkpath)):
        remove(linkpath)
        request_handler.send_response(200)
        request_handler.end_headers()
    else:
        request_handler.send_response(404)
        request_handler.end_headers()

def exec_remove_shares(request_handler):
    shareid = int(request_handler.path.replace('/lox_api/shares/', '', 1).replace('/revoke', '',1))
    sql = 'remove from shares where id = ?'
    database_execute(sql, (shareid))
    request_handler.send_response(200)
    request_handler.end_headers()


def exec_edit_shares(request_handler):
    shareid = request_handler.path.replace('/lox_api/shares/', '', 1).replace('/edit', '',1)
    share = get_share_by_id(shareid)
    json = get_body_json(request_handler)
    symlinks = SymlinkCache()
    path = share.item.path
    links = symlinks.get(path)
    # TODO: clean old links
    bindpoint = ConfigSingleton().get('filesystem', 'bindpoint')
    for entry in json:
        to_file = join(bindpoint, entry.title, basename(entry.path))
        symlink(path, to_file)
    

def exec_shares(request_handler):
    """
    Handle share information  
    """
    path2 = request_handler.path.replace('/lox_api/shares/', '', 1)

    request_handler.send_response(200)
    request_handler.end_headers()

    data = list_share_items(path2)
    request_handler.wfile.write(data)

def exec_invitations(request_handler):
    """
    Handle invitation listing
    """
    request_handler.send_response(200)
    request_handler.end_headers()
    request_handler.wfile.write(get_database_invitations(request_handler.user))

def exec_invite_accept(request_handler):
    """
    Accepts/reopens an invitation to filesharing.
    """
    result = toggle_invite_state(request_handler, 'accepted')
    if result:
        request_handler.send_response(200)
    else:
        request_handler.send_response(404)
    request_handler.end_headers()

def exec_invite_reject(request_handler):
    """
    Rejects/cancels an invitation to filesharing.
    """
    result = toggle_invite_state(request_handler, 'rejected')
    if result:
        request_handler.send_response(200)
    else:
        request_handler.send_response(404)

    request_handler.end_headers()


def exec_files_path(request_handler):
    """
    # 2 POST /lox_api/files/{path}    
    # Upload file '{path}' naar de localbox server. {path} is een relatief file path met urlencoded componenten (e.g.: path/to/file%20met%20spaties).
    """        
    path = request_handler.path.replace('/lox_api/files/', '', 1)
    if path != '':
        path = localbox_path_decoder(path)      
    filepath = get_filesystem_path(path, request_handler.user)
    if (request_handler.command=="POST"):
        filedescriptor = open(filepath, 'wb')
        length = int(request_handler.headers.get('content-length'))
        filedescriptor.write(request_handler.rfile.read(length))

    if (request_handler.command=="GET"):
        if isdir(filepath):
            for path, directories, files in walk(filepath):
                break
            #path, directories, files = walk(filepath).next()
            dirdict = stat_reader(path, request_handler.user)
            dirdict['children'] = []
            for child in directories + files:
                childpath = join(filepath, child)
                dirdict['children'].append(stat_reader(childpath, request_handler.user))
            request_handler.wfile.write(dumps(dirdict))
        else:
            filedescriptor = open(filepath, 'rb')
            request_handler.wfile.write(filedescriptor.read())

def exec_operations_create_folder(request_handler):
    length = int(request_handler.headers.get('content-length'))
    json_object = loads(request_handler.rfile.read(length))
    bindpoint = ConfigSingleton().get('filesystem', 'bindpoint')
    filepath = join(bindpoint, request_handler.user, json_object['path'])
    if lexists(filepath):
        request_handler.send_response(404)
        request_handler.end_headers()
        request_handler.wfile.write("Error: Something already exits at path")
        return
    mkdir(filepath)

def exec_operations_delete(request_handler):
    length = int(request_handler.headers.get('content-length'))
    json_object = loads(request_handler.rfile.read(length))
    bindpoint = ConfigSingleton().get('filesystem', 'bindpoint')
    filepath = join(bindpoint, request_handler.user, json_object['path'])
    if not exists(filepath):
        request_handler.send_response(404)
        request_handler.end_headers()
        request_handler.wfile.write("Error: No file exits at path")
        return
    remove(filepath)
    SymlinkCache().remove(filepath)

def exec_operations_move(request_handler):
    length = int(request_handler.headers.get('content-length'))
    json_object = loads(request_handler.rfile.read(length))
    bindpoint = ConfigSingleton().get('filesystem', 'bindpoint')
    move_from = join(bindpoint, request_handler.user, json_object['from_path'])
    move_to = join(bindpoint, request_handler.user, json_object['to_path'])
    if not isfile(move_from):
        request_handler.send_response(404)
        request_handler.end_headers()
        request_handler.wfile.write("Error: No file exits at from_path")
        return
    if lexists(move_to):
        request_handler.send_response(404)
        request_handler.end_headers()
        request_handler.wfile.write("Error: A file already exists at to_path")
        return
    move(move_from, move_to)
    

# 10 POST /lox_api/operations/copy
#    Kopieert een file van from_path naar to_path en retourneert of het succesvol is.
#    De volgende velden moeten bij de call aanwezig zijn.
#    - from_path: pad naar de file die gekopieert moet worden
#    - to_path: locatie waar de nieuwe file neergezet moet worden.
#    retourneert 200 in geval van succes, 404 in geval van falen.
def exec_operations_copy(request_handler):
    """
    # Kopieert een file van from_path naar to_path en retourneert of het succesvol is.
    """
    
    length = int(request_handler.headers.get('content-length'))
    json_object = loads(request_handler.rfile.read(length))
    bindpoint = ConfigSingleton().get('filesystem', 'bindpoint')
    copy_from = join(bindpoint, request_handler.user, json_object['from_path'])
    copy_to = join(bindpoint, request_handler.user, json_object['to_path'])
    if not exists(copy_from):
        request_handler.send_response(404)
        request_handler.end_headers()
        request_handler.wfile.write("Error: No file exits at from_path")
        return
    if lexists(copy_to):
        request_handler.send_response(404)
        request_handler.end_headers()
        request_handler.wfile.write("Error: A file already exists at to_path")
        return
    copyfile(copy_from, copy_to)

    request_handler.send_response(200)
    request_handler.end_headers()


    """
    # 29 POST /lox_api/user   # 13
    """    
def exec_user(request_handler):
    # TODO: this is the function to SEND encryption keys, dummy!
    print ("running exec user")
    sql = "select public_key, private_key from users where name = ?"
    result = database_execute(sql, (request_handler.user,))[0]
    result_dictionary = {'user':request_handler.user, 'public_key': result[0], 'private_key':result[1]}
    
    request_handler.wfile.write(dumps(result))


    """
    # 30 GET /lox_api/user/{username}   # 14
    """   
# Return een JSON dictionary met gebruikersinformatie.
# Indien er geen gebruikersnaam meegegeven is met het request wordt de info van de huidige user gebruikt.
# De velden in dit dictionary zijn 'name', 'public_key' en 'private_key'.
# De 'private_key' wordt alleen meegestuurd voor de ingelogde gebruiker.
#
# Deze keys worden gebruikt om bestanden mee te encrypten.
# In het geval van de 'private_key' gaat het om een de key om mee de decoderen.

def exec_user_username(request_handler):
    username = request_handler.path.replace('/lox_api/user/', '', 1)
    if username == request_handler.user:
        sql = 'select public_key, private_key from users where name = ?;'
    else:
        sql = 'select public_key from users where name = ?;'

    result = database_execute(sql, (username,))
    if result == []:
        request_handler.send_response(404)
        request_handler.end_headers()
        request_handler.wfile.write("Unknown user")
        return
    else:
        request_handler.send_response(200)
        request_handler.end_headers()

    info = {'name': username, 'public_key':result[0]}
    if username == request_handler.user:
        info['private_key'] = result[1]
    request_handler.wfile.write(dumps(info))
    

def exec_create_share(request_handler):
    length = int(request_handler.headers.get('content-length'))
    body = request_handler.rfile.read(length)
    json_list = loads(body)
    path2 = request_handler.path.replace('/lox_api/share_create/', '', 1)
    bindpoint = ConfigSingleton().get('filesystem', 'bindpoint')
    sender = request_handler.user
    from_file = join(bindpoint, sender, path2)
    # TODO: something something group
    share = Share(sender, None, ShareItem(path=path2))
    share.save_to_database()
    for json_object in json_list:
        if json_object['type'] == 'user':
            receiver = json_object['username']
            to_file = join(bindpoint, receiver, path2)
            if exists(to_file):
                print("destination " + to_file + " exists.")
                request_handler.send_response(500)
                return
            if not exists(from_file):
                print("source " + from_file + "does not exist.")
                request_handler.send_response(500)
                return
            symlink(from_file, to_file)
            invite = Invitation(None, 'pending', share, sender, receiver)
            invite.save_to_database()
    request_handler.send_response(200)

def exec_key(request_handler):
    localbox_path = request_handler.path.replace('/lox_api/key/', '', 1)
    if request_handler.command == "GET":
        key, iv = get_key_and_iv(localbox_path, user)
        request_handler.wfile.write(dumps({'key': key, 'iv': iv}))
    elif request_Handler.command == "POST":
        length = int(request_handler.headers.get('content-length'))
        data = request_handler.rfile.read(length)
        json_object = loads(data)
        sql = "insert into keys (path, user, key, iv) VALUES (?, ?, ?)"
        result = database_execute(sql, (localbox_path, json_object['key'], json_object['iv']))

def exec_key_revoke(request_handler):
    path = request_handler.path.replace('/lox_api/key_revoke/', '', 1)
    lengthstring = request_handler.headers.get('content-length')
    if lengthstring is None:
        user = request_handler.user
    else:
        data = request_handler.rfile.read(int(lengthstring))
        user = loads(data)['username']
        # Let's either not allow users to add a username or not ave the restriction that they cannot get the data back next time
        if user != request_handler.user:
            request_handler.send_response(403)
    sql = 'remove from keys where user = ? and path = ?;'
    database_execute(sql, (user, path))

def exec_meta(request_handler):
    path = request_handler.path.replace('/lox_api/meta/', '', 1)
    result = stat_reader(get_filesystem_path(path, request_handler.user), request_handler.user)
    request_handler.wfile.write(dumps(result))
    request_handler.send_response(200)
    request_handler.end_headers()

def fake_login(request_handler):
    form = """ <form action="login_check" method="POST"> <input type="submit" value="signin"> </form>"""
    request_handler.wfile.write(form)
    request_handler.send_response(200)
    request_handler.end_headers()

def fake_login_check(request_handler):
    html = """<meta http-equiv="refresh" content="1,url=/register_app /><a href="/register_app">next</a>"""
    request_handler.send_header('Location', '/register_app')
    request_handler.send_response(302)
    request_handler.end_headers()
    request_handler.wfile.write(html)
    
def fake_register_app(request_handler):
    result = { 'baseurl':'https://localhost:8000/', 'name':'schimmelpenning', 'user':'user', 'logourl':'https://8ch.net/static/logo_33.svg', 'BackColor':'#0000FF', 'FontColor': '#FF0000', 'APIKeys':[{'Name':'LocalBox iOS', 'Key':'keystring', 'Secret':'secretstring'}], 'pin_cert':'MIIDVzCCAj+gAwIBAgIJAKn6Bcf2mTH+MA0GCSqGSIb3DQEBCwUAMEIxCzAJBgNVBAYTAlhYMRUwEwYDVQQHDAxEZWZhdWx0IENpdHkxHDAaBgNVBAoME0RlZmF1bHQgQ29tcGFueSBMdGQwHhcNMTUwOTE1MTAyODM3WhcNMTYwOTE0MTAyODM3WjBCMQswCQYDVQQGEwJYWDEVMBMGA1UEBwwMRGVmYXVsdCBDaXR5MRwwGgYDVQQKDBNEZWZhdWx0IENvbXBhbnkgTHRkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuhdfwhBc0pIaRxeq4+xv6WZVIb0PSbW8G6kJ7kbw+NL0s+FS+Au0JQNtOqauiYdi09ejqfHHUW+cLoX3qMeH2Wgr9TuIbRamLOJw/twstq0LqKOjaiLgq/xRNcUrqptgDfXSbBQXRcGsdB+6E6pKGfViDIZzhdgImXKqROfa6Yv5aGHuz204sKovu2/gSHPz2IDXSdAehpNbJ5ORFP3+Gkb1z6VoZvJ5QAp/+Ri3th8ms6o/DXRhwSCtetKQshyRjYXpea3v/Oq9lbzBm43LhzyH24ThwKKX8p1JtCJcMfHzpa9OHgLNpDDp4AKCcq5KcDRWJxoTDs45Noj/j3PtlQIDAQABo1AwTjAdBgNVHQ4EFgQUibXrIXzSfhlh/ndNG4cMjIHg3v8wHwYDVR0jBBgwFoAUibXrIXzSfhlh/ndNG4cMjIHg3v8wDAYDVR0TBAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAQEALEzFqDhRgiRWxJJx3CwG41VadNYJxxgvVos0sVc4y7fTWG2Rq42mMVbMGBvqxtz69KwcHGAvfC1DteEdTSHmEuhsR4DiX0mChfNQrWvrbDTnKaa00aaWArVMUGa+vbDFxsW+r0Z+hzBneQI9Qiy8dexUD3etV7EIumijEfaPDvMDNnwwVGj17D7EXY/aDgFQqwTiPGlzOE73kcFTzkMMRzkNhurcNbhp/Z92ToL92LgetAVIrMNysWrgCJrI/gh7nPZIX6LH5TD0Erlx/NEP5IKcsVUnIxH+aXQD4sHjreiUxdPpuqsAy3u4ThMI+o5Rj6Iq1M5L8sPjJ6WzkEXblw==', "access_token": "2DHJlWJTui9d1pZnDDnkN6IV1p9Qq9", "token_type": "Bearer", "expires_in": 600, "refresh_token": "tNXAVVo2QE7c5MKgFCB1mKuAPsu4xL", "scope": "all"}
    request_handler.send_response(200)
    request_handler.send_header('PHPSESSID', 'padding')
    request_handler.send_header('Domain', '10.42.0.1')
    request_handler.end_headers()
    request_handler.wfile.write(dumps(result))

def fake_oauth(request_handler):
    if request_handler.command != "POST":
        html="""<html><head></head><body><form action="/oauth2/v2/auth" method=POST><input type="submit" value="allow"></form></body></html>"""
        request_handler.send_response(200)
        request_handler.send_header('Content-type', 'text/html')
        request_handler.end_headers()
        request_handler.wfile.write(html)
    else:
        request_handler.send_response(302)
        request_handler.send_header('Location', 'lbox://oauth-return?code=pony')
        request_handler.end_headers()
        result = { "access_token": "2DHJlWJTui9d1pZnDDnkN6IV1p9Qq9", "token_type": "Bearer", "expires_in": 600, "refresh_token": "tNXAVVo2QE7c5MKgFCB1mKuAPsu4xL", "scope": "all"}
        request_handler.wfile.write(result)

def exec_identities(request_handler):
    sql = 'select name from users';
    result = database_execute(sql)
    outputlist = []
    for entry in result:
        outputlist.append({'id': entry[0], 'name': entry[0], 'type':'user'})
    request_handler.wfile.write(dumps(outputlist))

def test(request_handler):
    request_handler.wfile.write(prepare_string("this is a log of wfile writing"))

ROUTING_LIST = [
    (regex_compile(r"\/lox_api\/files\/.*"), exec_files_path),
    (regex_compile(r"\/lox_api\/invitations"), exec_invitations),
    (regex_compile(r"\/lox_api\/invite/[0-9]+/accept"), exec_invite_accept),
    (regex_compile(r"\/lox_api\/invite/[0-9]+/revoke"), exec_invite_reject),
    (regex_compile(r"\/lox_api\/operations\/copy"), exec_operations_copy),
    (regex_compile(r"\/lox_api\/operations\/move"), exec_operations_move),
    (regex_compile(r"\/lox_api\/operations\/delete"), exec_operations_delete),
    (regex_compile(r"\/lox_api\/operations\/create_folder"), exec_operations_create_folder),
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

    (regex_compile(r"\/test.*"), test),
    (regex_compile(r"\/login"), fake_login),
    (regex_compile(r"\/login_check"), fake_login_check),
    (regex_compile(r"\/register_app"), fake_register_app),
    (regex_compile(r"\/oauth.*"), fake_oauth),
]

