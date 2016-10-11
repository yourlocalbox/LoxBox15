import os

import config


def get_bindpoint():
    bindpoint = os.path.expandvars(config.ConfigSingleton().get('filesystem', 'bindpoint'))
    return bindpoint
