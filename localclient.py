import random
import time
import json
import sys
import httplib
from urlparse import urlparse

from lib.http import urlopen
from lib.cache import LocalCache

URLS = 'urls4.txt'
REQS = 1000
VERBOSE = False


CACHE = LocalCache()

def cached(fn):
    def inner(obj, url):
        doc = CACHE.get(url, None)
        if doc is None:
            print 'x',
            doc = fn(obj, url)
            CACHE.set(url, doc)
        else:
            print '.',
        return doc
    return inner


class BaseClient(object):
    def __init__(self):
        self.verbose = False

    def fetch(self, url):
        res = urlopen(url, timeout=60)
        if res.code == 200:
            return res.read()
        return ''


class CachedClient(BaseClient):
    @cached
    def fetch(self, url):
        return super(CachedClient, self).fetch(url)


class KeepAliveClient(BaseClient):
    def __init__(self, *args, **kwargs):
        super(KeepAliveClient, self).__init__(*args, **kwargs)
        self._connections = {}

    def fetch(self, url):
        url = urlparse(url)

        q = url.path
        if url.query:
            q += '?' + url.query

        conn = self.get_connection(url.hostname, url.port)
        conn.request('GET', q)

        try:
            res = conn.getresponse()
        except httplib.BadStatusLine:
            self.close_connection(url.hostname, url.port)
            conn = self.get_connection(url.hostname, url.port)
            conn.request('GET', q)
            res = conn.getresponse()

        if res.status == 200:
            return res.read()
        return ''

    def get_connection(self, host, port):
        key = host + ':' + str(port)
        conn = self._connections.get(key, None)
        if conn is None:
            conn = httplib.HTTPConnection(host, port)
            self._connections[key] = conn
        return conn

    def close_connection(self, host, port):
        key = host + ':' + str(port)
        if key in self._connections:
            self._connections[key].close()
            del(self._connections[key])


def test(cl, urls):
    begin = time.time()
    cl.verbose = VERBOSE
    for x in xrange(REQS):
        if VERBOSE:
            print x
        url = random.choice(urls)
        _ = cl.fetch(url)
    end = time.time()
    elapsed = end - begin
    return '%d requests in %.3f seconds (%.1f reqs/sec)' % (REQS, elapsed, (REQS / elapsed))


if __name__ == '__main__':
    urls = []
    with open(URLS, 'r') as f:
        for l in f:
            urls.append(l.strip())

    cl = BaseClient()
    res = test(cl, urls)
    print "BaseClient: %s" % (res)

    #cl = CachedClient()
    #res = test(cl, urls)
    #print "CachedClient: %s" % (res)
