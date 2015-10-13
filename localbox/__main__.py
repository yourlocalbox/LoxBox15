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
    if signum == SIGINT:
        getLogger('api').info('SIGINT received, shutting down')
        # TODO: Graceful shutdown that lets people finish their things
        sysexit(1)


def run():
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
