from ssl import SSLContext
from ssl import PROTOCOL_TLSv1_2 as SSL_PROTOCOL
from logging import getLogger

from localbox import config
from localbox.cache import TimedCache

try:
    from urllib2 import HTTPError
    from urllib import urlencode  # pylint: disable=E0611
    from urllib2 import Request
    from urllib2 import urlopen
except ImportError:
    from urllib.error import HTTPError  # pylint: disable=E0611,F0401
    from urllib.parse import urlencode  # pylint: disable=E0611,F0401
    from urllib.request import Request  # pylint: disable=E0611,F0401
    from urllib.request import urlopen  # pylint: disable=E0611,F0401


def authorize(func):
    """
    Decorator for checking if the user has authorization before executing the request_handler.
    If the user has authorization the request_handler is executed by the decorator.
    Otherwise the user will receive the authentication url as response; sent by
    :py:func:`~localbox.LocalBoxHTTPRequestHandler.wrap_request` via
    :py:func:`~localbox.LocalBoxHTTPRequestHandler.send_response`

    :param func: method in :py:class:`~localbox.LocalBoxHTTPRequestHandler` that requires authorization
    :return:
    """

    def check(request_handler):
        request_handler.user = check_authorization(request_handler)

        if not request_handler.user:
            request_handler.status = 401

            if request_handler.back_url:
                querystring = urlencode({'redirect_uri': request_handler.back_url})
            else:
                querystring = urlencode({'redirect_uri': request_handler.protocol
                                                         + request_handler.headers['Host']
                                                         + request_handler.path})

            redirect_url = config.get('oauth', 'redirect_url') + "?" + querystring
            getLogger(__name__).debug('redirect_url: %s' % redirect_url, extra=request_handler.get_log_dict())
            request_handler.new_headers['WWW-Authenticate'] = 'Bearer domain="' + redirect_url + '"'
            request_handler.body = "<h1>401: Forbidden.</h1>" \
                                   "<p>Authorization failed. Please authenticate at" \
                                   "<a href=\"{0}\">{1}</a></p>".format(redirect_url, redirect_url)
        else:
            func(request_handler)

    return check


def check_authorization(request_handler):
    """
    Assert whether the authorization header is valid by checking it against
    the cache first and if unsuccessful, the oauth server. Sets the 'user'
    field of the request_handler object.

    :return: When successful returns user's name. Returns None on failure.
    """
    auth_header = request_handler.headers.getheader('Authorization')
    if auth_header is None:
        getLogger('auth').debug("authentication failed: no Authorization header available",
                                extra=request_handler.get_log_dict())
        return None
    auth_url = config.get('oauth', 'verify_url')
    getLogger('auth').debug("verify_url: %s" % auth_url, extra=request_handler.get_log_dict())
    cache = TimedCache(timeout=0)  # FIXME: Cache is broken
    name = cache.get(auth_header)
    if name is not None:
        return name
    auth_request = Request(auth_url, None, {'Authorization': auth_header})
    try:
        ctx = SSLContext(SSL_PROTOCOL)
        response = urlopen(auth_request, context=ctx)
        name = response.read()
    except HTTPError as error:
        if error.code == 403:
            getLogger('auth').debug("authentication failed: Wrong/expired code",
                                    extra=request_handler.get_log_dict())
        else:
            getLogger('auth').debug("authentication failed: HttpError %s" % error,
                                    extra=request_handler.get_log_dict())
        name = ''
    if name == '':
        name = None
        getLogger('auth').debug('authentication failed: response %s' % name,
                                extra=request_handler.get_log_dict())
    else:
        getLogger('auth').debug('Authenticated user: ' + name,
                                extra=request_handler.get_log_dict())
        cache.add(auth_header, name)
    return name
