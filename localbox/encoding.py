"""
Encoding functions specific to localbox
"""
from json import JSONEncoder
try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote



class LocalBoxJSONEncoder(JSONEncoder):
    """
    JSONEncoder for localbox classes
    """
    def default(self, o):
        """
        The way objects are usually encoded into JSON.
        """
        if hasattr(o, 'to_json'):
            return o.to_json()
        return o.__dict__


def localbox_path_decoder(path):
    """
    A 'localbox_path' is a unix filepath with the urlencoded components.
    """
    realpath = []
    components = path.split('/')
    for component in components:
        realpath.append(unquote(component))
    return '/'.join(realpath)
