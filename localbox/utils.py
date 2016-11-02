import os

from localbox import config


def get_bindpoint():
    bindpoint = os.path.expandvars(config.get('filesystem', 'bindpoint'))
    return bindpoint


def get_logging_empty_extra():
    return {'user': None, 'ip': None, 'path': None}


def get_logging_extra(request_handler):
    return {'user': request_handler.user, 'ip': request_handler.client_address[0], 'path': request_handler.path}