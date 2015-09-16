"""
LocalBox API Implementation module
"""
from json import dumps
from re import compile as regex_compile

from .shares import list_share_items
from .database import database_execute

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


ROUTING_LIST = [
    (regex_compile(r"\/lox_api\/invitations"),
     exec_invitations),
    (regex_compile(r"\/lox_api\/user"), exec_user),
    (regex_compile(r"\/lox_api\/shares\/.*"), exec_shares),
]

