"""
Start the LocalBox server
"""
from localbox import main
from logging import DEBUG
from logging import StreamHandler, FileHandler
from logging import Formatter

from .config import prepare_logger
from .config import ConfigSingleton


def run():
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
