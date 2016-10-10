import os, logging

import config, logging_utils


def get_bindpoint():
    bindpoint = os.path.expandvars(config.ConfigSingleton().get('filesystem', 'bindpoint'))
    return bindpoint


def mkdir_p(path):
    """
    Similar to mkdir -p
    :param path:
    :return:
    """

    if os.path.exists(path):
        logging.getLogger(__name__).debug('%s already exists' % path, extra=logging_utils.get_logging_empty_extra())
        return

    par = os.path.split(path)[0]
    if os.path.exists(par):
        os.mkdir(path)
        logging.getLogger(__name__).debug('mkdir: %s' % path, extra=logging_utils.get_logging_empty_extra())
    else:
        mkdir_p(par)
        logging.getLogger(__name__).debug('mkdir: %s' % path, extra=logging_utils.get_logging_empty_extra())
        os.mkdir(path)
