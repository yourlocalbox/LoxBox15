"""
Encoding functions specific to localbox
"""
from os.path import join
from json import JSONEncoder
try:
    from urllib import unquote  # pylint: disable=E0611
except ImportError:
    from urllib.parse import unquote  # pylint: disable=E0611,F0401


class LocalBoxJSONEncoder(JSONEncoder):
    """
    JSONEncoder for localbox classes
    """
    def default(self, o):  # pylint: disable=E0202
        """
        The way objects are usually encoded into JSON.
        @param o the object to encode into json
        @return the json equivalent of 'o'
        """
        if hasattr(o, 'to_json'):
            return o.to_json()
        return o.__dict__


def localbox_path_decoder(path):
    """
    A 'localbox_path' is a unix filepath with the urlencoded components.
    @param path a 'localbox_path' of which to urldecode the components
    @return the localbox path without urlencoded components
    """
    realpath = []
    components = path.split('/')
    for component in components:
        if component != '':
            realpath.append(unquote(component))
    newpath = join(*realpath)
    return newpath
