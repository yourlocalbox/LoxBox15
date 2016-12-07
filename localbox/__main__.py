"""
Start the LocalBox server
"""
import logging
from logging import getLogger
from signal import SIGINT, signal
from sys import exit as sysexit, stdout

import localbox.utils
from loxcommon.log import prepare_logging
from .__init__ import main
from loxcommon.config import ConfigSingleton
from loxcommon import os_utils


def sig_handler(signum, frame):  # pylint: disable=W0613
    """
    Handle POSIX signal signum. Frame is ignored.
    """
    if signum == SIGINT:
        getLogger('api').info('SIGINT received, shutting down',
                              extra={'user': None, 'ip': None, 'path': None})
        # TODO: Graceful shutdown that lets people finish their things
        sysexit(1)
    else:
        getLogger('api').info('Verbosely ignoring signal ' + str(signum),
                              extra={'user': None, 'ip': None, 'path': None})


def run():
    """
    readies the signal handler, configures the logging and starts the
    HTTPServer component of LocalBox
    """
    signal(SIGINT, sig_handler)
    main()


if __name__ == '__main__':
    configparser = ConfigSingleton('localbox', defaults={'console': False})
    prepare_logging(configparser)

    logging.Logger.manager.loggerDict[os_utils.__name__] = logging.LoggerAdapter(
        logging.getLogger(os_utils.__name__),
        localbox.utils.get_logging_empty_extra())
    run()
