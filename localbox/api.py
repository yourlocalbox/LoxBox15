"""
LocalBox API Implementation module
"""
from json import dumps
from json import loads
from re import compile as regex_compile
from os import symlink
from os.path import join
from os.path import exists

from .shares import Share, ShareItem, Invitation
from .shares import list_share_items
from .shares import get_database_invitations
from .encoding import localbox_path_decoder
from .shares import toggle_invite_state
from .config import ConfigSingleton

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
    if (request_handler.command=="POST"):
        print ("Running files path :  2 POST /lox_api/files/{path}")  
        """
        A 'localbox_path' is a unix filepath with the urlencoded components.
        """
        points = ".."
        bindpoint = request_handler.bindpoint.user.path   # "\/lox_api\/files\/.*"
        wfile     = request_handler.rfile
        
        localbox_path_decoder(points+bindpoint+wfile)      
        request_handler.wfile.write(dumps(info))
        
    """
    # 20 GET /lox_api/files/{path}
    # Download file '{path}' naar de localbox server. {path} is een relatief file path met urlencoded componenten (e.g.: path/to/file%20met%20spaties).
    """
    if (request_handler.command=="GET"):
        print ("Running files path :  20 GET /lox_api/files/{path}")

        puntjes = ".."
        bindpoint = request_handler.bindpoint.user.path   # "\/lox_api\/files\/.*"
        rfile     = request_handler.rfile

        localbox_path_decoder(points+bindpoint+rfile)  
        request_handler.rfile.read(dumps(info))


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
    request_handler.from_path,
    request_handler.to_path
    bindpoint = configparser.get('httpd', 'bindpoint')
    user = request_handler.user

    print("Running operations copy : 10 POST /lox_api/operations/copy")
    request_handler.send_response(200)
    request_handler.end_headers()


    """
    # 29 POST /lox_api/user   # 13
    """    
def exec_user(request_handler):
    print ("running exec user")
    # Haal name, public_key, private_key from user uit database.
    if (request_handler.user): # is user loggen in ?
        sql = "select name, public_key, private_key from user where user = request_handler.user"
    result = database_execute(sql, (request_handler.user,))    
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
    print ("running exec user username")
#   get info below from DB, private_key only if user is logged in.
    if (request_handler.user): # is user loggen in ?
        sql = "select name, public_key, private_key from user where user = request_handler.user"
    result = database_execute(sql, (user,)) 

    info = {'name':'result.user', 'public_key':'result.public_key', 'private_key':'private_key'}
    request_handler.wfile.write(dumps(result))
    
from pprint import pprint

def exec_create_share(request_handler):
    length = int(request_handler.headers.getheader('content-length'))
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

ROUTING_LIST = [
    (regex_compile(r"\/lox_api\/files\/.*"), exec_files_path),
    (regex_compile(r"\/lox_api\/invitations"), exec_invitations),
    (regex_compile(r"\/lox_api\/invite/[0-9]+/accept"), exec_invite_accept),
    (regex_compile(r"\/lox_api\/invite/[0-9]+/reject"), exec_invite_reject),
    (regex_compile(r"\/lox_api\/operations\/copy"), exec_operations_copy),
    (regex_compile(r"\/lox_api\/share_create\/.*"), exec_create_share),
    (regex_compile(r"\/lox_api\/shares\/.*"), exec_shares),
    (regex_compile(r"\/lox_api\/user"), exec_user),
    (regex_compile(r"\/lox_api\/user_username"), exec_user_username),  
]

