"""
Encoding functions specific to localbox
"""
from datetime import datetime
from os.path import join
from os.path import split
from os.path import abspath
from os.path import relpath
from os.path import isdir
from os.path import islink
from logging import getLogger
from sys import exit as sysexit
from os import chdir
from os import getcwd
from os import stat
from os import walk

from localbox.database import database_execute
from localbox.utils import get_bindpoint
import localbox.logging_utils as logging_utils

try:
    from os import readlink
except ImportError:
    def readlink(var):
        raise NotImplementedError(var)
from os import sep

from .config import ConfigSingleton


def get_filesystem_path(localbox_path, user):
    """
    Given a LocalBox path (e.g. '/file_name'), return the corresponding
    filesystem path (e.g. '/var/localbox/data/user/file_name')
    @param localbox_path the path relative to localbox' view
    @param user the user for which to translate the path (the username is part
           of the path and hence cannot be ommitted.
    @return a filesystem path to the resource pointed to by the localbox path
    """
    while localbox_path.startswith('/'):
        localbox_path = localbox_path[1:]
    if ".." in localbox_path.split('/'):
        raise ValueError("No relative paths allowed in localbox")
    bindpoint = get_bindpoint()
    filepath = join(bindpoint, user, localbox_path)
    getLogger(__name__).debug('filesystem path: %s' % filepath, extra=logging_utils.get_logging_empty_extra())
    return filepath


def get_bindpoint_user(user):
    return abspath(join(get_bindpoint(), user))


def get_localbox_path(filesystem_path, user):
    localboxpath = '/' + join(relpath(filesystem_path,
                                      get_bindpoint_user(user))).replace(sep, '/')

    if localboxpath == '/.':
        localboxpath = '/'

    return localboxpath


def get_key_path(user, localbox_path=None, filesystem_path=None):
    if localbox_path is not None:
        return localbox_path
    return get_localbox_path(filesystem_path, user)[1:].split('/')[0]


def stat_reader(filesystem_path, user):
    """
    Return metadata for the given (filesystem) path based on information
    provided by the stat system call.
    @param filesystem_path a path referring to the file to stat
    @param user the user for which to reutrn the info
    @return a dictionary of metadata for the filesystem path given
    """
    getLogger(__name__).debug('read stats for file: %s' % filesystem_path, extra=logging_utils.get_logging_empty_extra())
    bindpath_user = get_bindpoint_user(user)
    if bindpath_user == abspath(filesystem_path):
        title = 'Home'
    else:
        title = [
            item for item in split(filesystem_path) if item != ''][-1]

    localboxpath = get_localbox_path(filesystem_path, user)
    keypath = get_key_path(user, filesystem_path=filesystem_path)

    sql = 'select 1 from keys where path=?;'
    result = database_execute(sql, (keypath,))
    has_keys = True if result and len(result) > 0 else  False

    try:
        statstruct = stat(filesystem_path)
    except OSError:
        return None
    statdict = {
        'title': title,
        'is_dir': isdir(filesystem_path),
        'modified_at': datetime.fromtimestamp(statstruct.st_mtime).isoformat(),
        'is_share': SymlinkCache().exists(abspath(filesystem_path)),
        'is_shared': islink(abspath(filesystem_path)),
        'has_keys': has_keys,
        'path': localboxpath,
    }
    if statdict['is_dir']:
        statdict['icon'] = 'Folder'
    else:
        statdict['icon'] = 'File'
    # if isdir(filesystem_path):
    #    statdict['hash'] = 'TODO'
    return statdict


class SymlinkCache(object):
    """
    Singleton keeping track of all symlinks (shares)
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SymlinkCache, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def remove(self, absolute_filename):
        """
        removes links to and from filename (from the cache)
        @param absolute_filename the file to remove from the cache
        """
        if absolute_filename in self.cache.keys():
            self.cache.pop(absolute_filename)
        for key, value in self.cache.items():
            if absolute_filename in value:
                newvalue = value.remove(absolute_filename)
                self.cache[key] = newvalue

    def exists(self, absolute_file_name):
        """
        Check whether absolute_file_name is in the cache, and thus a
        destination of a symlink and thus a 'share' folder
        @param absolute_file_name name of the file to check in the cache
        """
        return absolute_file_name in self.cache

    def get(self, path):
        """
        Returns a list of sources of a symlink destination from the cache
        @param path a file which is symlinked to
        @return a list of symlinks to that file
        """
        return self.cache[path]

    def __init__(self, path=None):
        if not hasattr(self, 'cache'):
            getLogger().info("initialising SymlinkCache", extra={'user': None, 'ip': None, 'path': None})
            self.cache = {}
            self.build_cache(path)
            getLogger().info("initialised SymlinkCache", extra={'user': None, 'ip': None, 'path': None})

    def __iter__(self):
        for entry in set(self.cache.keys()):
            yield entry

    def build_cache(self, path=None):
        """
        Build the reverse symlink cache by walking through the filesystem and
        finding all symlinks and put them into a cache dictionary for reference
        later.
        """
        working_directory = getcwd()
        if path is None:
            bindpoint = get_bindpoint()
            if bindpoint is None:
                getLogger('files').error("No bindpoint found in the filesystem "
                                         "section of the configuration file, "
                                         "exiting")
                sysexit(1)
        else:
            bindpoint = path
        for dirname, directories, files in walk(bindpoint):
            for entry in directories + files:
                linkpath = abspath(join(dirname, entry))
                if islink(linkpath):
                    chdir(dirname)
                    destpath = abspath(readlink(linkpath))
                    if destpath in self.cache:
                        self.cache[destpath].append(linkpath)
                    else:
                        self.cache[destpath] = [linkpath]
        chdir(working_directory)
