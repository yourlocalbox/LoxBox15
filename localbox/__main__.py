"""
Start the LocalBox server
"""
from localbox import main
from logging import getLogger
from logging import StreamHandler

if __name__ == '__main__':
    LOG = getLogger("database")
    LOG.setLevel(-1)
    LOG.addHandler(StreamHandler())
    main()
