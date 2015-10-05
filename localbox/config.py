"""
Module holding configuration and configparser related functions
"""

try:
    from ConfigParser import ConfigParser
    from ConfigParser import NoOptionError, NoSectionError
except ImportError:
    from configparser import ConfigParser
    from configparser import NoOptionError, NoSectionError


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
        if not hasattr(self, 'configparser'):
            self.configparser = ConfigParser()
            if not location:
                self.configparser.read(['/etc/localbox.ini', '~/localbox.ini',
                                        '~/.config/localbox/config.ini',
                                        'localbox.ini'])
            else:
                self.configparser.read(location)

    def get(self, section, field, default=None):
        """
        Returns the value of a certain field in a certain section on the
        configuration
        """
        try:
            result = self.configparser.get(section, field)
        except (NoOptionError, NoSectionError):
            result = default
        return result

    def getboolean(self, section, field, default=None):
        """
        Returns the value of a certain field in a certain section on the
        configuration in a boolean context
        """
        try:
            result = self.configparser.getboolean(section, field)
        except (NoOptionError, NoSectionError):
            result = default
        return result

    def getint(self, section, field):
        """
        Returns the value of a certain field in a certain section on the
        configuration, cast to an int.
        """
        return self.configparser.getint(section, field)
