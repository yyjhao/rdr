import urlnorm
import httplib
from urllib import urlencode
from urlparse import urlparse, urlunparse, parse_qs, urljoin

REMOVABLE_QUERIES = set([
    'utm_content',
    'utm_medium',
    'utm_source',
    'utm_campaign',
    'showComment',
    'ncid',
    'ocid',
    'feedType',
    'feedName',
])


def remove_redundant_queries(url):
    url_obj = urlparse(url)
    query = parse_qs(url_obj.query)

    new_query = {
        k: v
        for k, v in query.items()
        if k not in REMOVABLE_QUERIES
    }

    return urlunparse(url_obj._replace(query=urlencode(new_query, True)))


def normalize_url(url):
    try:
        return urlnorm.norm(remove_redundant_queries(unshorten_url(url)))
    except Exception as e:
        print 'fail to normalize url', url, e
        return url


def unshorten_url(url):
    url_idna = url.encode('UTF-8')
    parsed = urlparse(url_idna)
    if parsed.scheme == 'http':
        h = httplib.HTTPConnection(parsed.netloc)
    elif parsed.scheme == 'https':
        h = httplib.HTTPSConnection(parsed.netloc)
    else:
        return url
    h.request('HEAD', url_idna)
    try:
        response = h.getresponse()
    except Exception as e:
        return url
    if response.status/100 == 3 and response.getheader('Location'):
        location = response.getheader('Location')
        new_url = urlparse(location)
        if not new_url.netloc:
            host = response.getheader('Host') or parsed.netloc
            new_url = new_url._replace(netloc=host)
        if not new_url.scheme:
            scheme = parsed.scheme
            new_url = new_url._replace(scheme=scheme)
        return urlunparse(new_url)
    else:
        if response.status != 200:
            print response.status, 'failed!', url
        return url
