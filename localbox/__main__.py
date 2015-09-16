from localbox import main
from logging import getLogger
from logging import StreamHandler

if __name__ == '__main__':
    log = getLogger("database")
    log.setLevel(-1)
    log.addHandler(StreamHandler())
    main()

