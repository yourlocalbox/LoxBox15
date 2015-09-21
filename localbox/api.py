"""
LocalBox API Implementation module
"""
from json import dumps
from re import compile as regex_compile

from .shares   import list_share_items
from .encoding import localbox_path_decoder

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
    request_handler.wfile.write("invites")

def exec_user(request_handler):
    """
    Handle user info (or pretend to)
    """
    info = {'name': 'user', 'public_key': 'FT9CH-XVXW7',
            'private_key': 'RPR49-VDHYD', 'complete': 'No!'}
    request_handler.wfile.write(dumps(info))


def exec_files_path(request_handler):
    """
    # 2 POST /lox_api/files/{path}
    # Upload file '{path}' naar de localbox server. {path} is een relatief file path met urlencoded componenten (e.g.: path/to/file%20met%20spaties).
    """        
    if (request_handler.command=="POST"):
        print "Running files path :  2 POST /lox_api/files/{path}"
        s = "\/lox_api\/files\/.*"
        s.lstrip(".*")
   
        """
        A 'localbox_path' is a unix filepath with the urlencoded components.
        """
        localbox_path_decoder(s)  
        request_handler.wfile.write(dumps(info))
        
    """
    # GET /lox_api/files/{path}
    # Download file '{path}' naar de localbox server. {path} is een relatief file path met urlencoded componenten (e.g.: path/to/file%20met%20spaties).
    """      
    elif(request_handler.command=="GET"):
        pass


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
    user      = request_handler.user

    print "Running operations copy : 10 POST /lox_api/operations/copy"
    request_handler.send_response(200) 
    request_handler.end_headers()
    

ROUTING_LIST = [
    (regex_compile(r"\/lox_api\/invitations"),      exec_invitations),
    (regex_compile(r"\/lox_api\/user"),             exec_user),
    (regex_compile(r"\/lox_api\/shares\/.*"),       exec_shares),
    (regex_compile(r"\/lox_api\/files\/.*"),        exec_files_path),
    (regex_compile(r"\/lox_api\/operations\/copy"), exec_operations_copy),  
]

