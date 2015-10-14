"""
Module holding configuration and configparser related functions
"""

from logging import getLogger
from logging import StreamHandler
try:
    from ConfigParser import ConfigParser
    from ConfigParser import NoOptionError, NoSectionError
except ImportError:
    from configparser import ConfigParser  # pylint: disable=F0401
    # pylint: disable=F0401
    from configparser import NoOptionError, NoSectionError


def prepare_logger(name, loglevel=None, handlers=None):
    if handlers is None:
        handlers = [StreamHandler()]
    log = getLogger(name)
    log.setLevel(loglevel)
    for handler in handlers:
        log.addHandler(handler)


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
        @param section the [section] in which to look for the information
        @param field the name of the configuration item to read
        @param default Value to return when the config option can't be found
        @return the value of said configuration item
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
        @param section the [section] in which to look for the information
        @param field the name of the configuration item to read
        @param default Value to return when the config option can't be found
        @return the boolean value of said configuration item
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
        @param section the [section] in which to look for the information
        @param field the name of the configuration item to read
        @return the integer value of said configuration item
        """
        return self.configparser.getint(section, field)
