"""
Start the LocalBox server
"""
from logging import DEBUG
from logging import StreamHandler, FileHandler
from logging import Formatter
from logging import getLogger
from signal import SIGINT, signal
from sys import exit as sysexit

from .__init__ import main
from .config import prepare_logger
from .config import ConfigSingleton


def sig_handler(signum, frame):
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
    config = ConfigSingleton()
    formatter = Formatter('%(asctime)s %(ip)s %(user)s: %(message)s')
    logfile = config.get('logging', 'logfile')
    loghandlers = []
    if logfile is not None:
        handler = FileHandler(logfile)
        handler.setFormatter(formatter)
        loghandlers.append(handler)
    if config.getboolean('logging', 'console', False):
        handler = StreamHandler()
        handler.setFormatter(formatter)
        loghandlers.append(handler)
    prepare_logger('database', DEBUG, loghandlers)
    prepare_logger('api', DEBUG, loghandlers)
    main()


if __name__ == '__main__':
    run()
