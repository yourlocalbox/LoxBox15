from ConfigParser import ConfigParser
class ConfigSingleton(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigSingleton, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self, location=None):
        self.configparser = ConfigParser()
        if not location:
            self.configparser.read(['/etc/localbox.ini', '~/localbox.ini',
                                    '~/.config/localbox/config.ini',
                                    'localbox.ini'])
        else:
            self.configparser.read(location)

    def get(self, section, field):
        return self.configparser.get(section, field)

    def getint(self, section, field):
        return self.configparser.getint(section, field)

