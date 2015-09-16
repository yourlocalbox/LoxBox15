"""
Module holding configuration and configparser related functions
"""
from ConfigParser import ConfigParser


class ConfigSingleton(object):
    """
    Singleton which has all configruation related info.
    """
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
        """
        Returns the value of a certain field in a certain section on the
        configuration
        """
        return self.configparser.get(section, field)

    def getint(self, section, field):
        """
        Returns the value of a certain field in a certain section on the
        configuration, cast to an int.
        """
        return self.configparser.getint(section, field)

