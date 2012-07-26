import random
import time
import json
import sys
import httplib
from urlparse import urlparse

from lib.http import urlopen
from lib.cache import LocalCache

URLS = 'urls3.txt'
REQS = 100
VERBOSE = False


class BaseLocalClient(object):
    def __init__(self, cache_max_items=1000, ttl=60):
        self._cache = LocalCache(cache_max_items)
        self.ttl = ttl
        self.verbose = False

    def fetch(self, url):
        if self.verbose:
            print 'fetching url: %s' % str(url)
        doc = self._cache.get(url, None)
        if doc is None:
            if self.verbose:
                print '\tNot cached'
            doc = self.urlget(url)
            self._cache.set(url, doc, self.ttl)
        return doc

    def urlget(self, url):
        res = urlopen(url, timeout=60)
        if res.code == 200:
            doc = res.read()
            doc = json.loads(doc)
            return doc['response']
        return ''

    def status(self):
        st = {}
        st['cache_items'] = len(self._cache)
        st['cache_size'] = sys.getsizeof(self._cache)
        return st


class KeepAliveClient(BaseLocalClient):
    def __init__(self, *args, **kwargs):
        super(KeepAliveClient, self).__init__(*args, **kwargs)
        self._connections = {}

    def urlget(self, url):
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
            doc = res.read()
            doc = json.loads(doc)
            return doc['response']
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


class SimpleLocalClient(KeepAliveClient):
    def fetch_listing(self, url):
        url = url.replace('listing', 'fullListing')
        url = url.replace('v0.1', 'test/v0.1')
        return self.fetch(url)


class MultiRequestClient(KeepAliveClient):
    def __init__(self, cache_max_items=1000, ttl=60):
        super(MultiRequestClient, self).__init__(cache_max_items, ttl)
        self.subresources = ['country', 'state', 'city', 'image']

    def fetch_listing(self, url):
        doc = self.fetch(url)
        new_data = []
        for item_url in doc['data']:
            item_doc = self.fetch(item_url)
            for subres in self.subresources:
                if subres in item_doc['resources']:
                    subres_doc = self.fetch(item_doc['resources'][subres])
                    item_doc['data'][subres] = subres_doc['data']
            new_data.append(item_doc['data'])
        doc['data'] = new_data
        return doc


class MultiRequestFullCacheClient(MultiRequestClient):
    def fetch_listing(self, url):
        doc = self._cache.get(url, None)
        if doc is None:
            doc = super(MultiRequestFullCacheClient, self).fetch_listing(url)
            self._cache.set(url, doc, self.ttl)
        return doc


def test(cl, urls):
    begin = time.time()
    cl.verbose = VERBOSE
    for x in xrange(REQS):
        if VERBOSE:
            print x
        url = random.choice(urls)
        _ = cl.fetch_listing(url)
    end = time.time()
    return '%d requests in %.3f seconds' % (REQS, end - begin)


if __name__ == '__main__':
    urls = []
    with open(URLS, 'r') as f:
        for l in f:
            urls.append(l.strip())

    scl = SimpleLocalClient(10000, 900)
    res = test(scl, urls)
    st = scl.status()
    print "SimpleLocalClient (QJT full doc): %s (items: %d, size: %s)" % (res, st['cache_items'], st['cache_size'])

    mcl = MultiRequestClient(10000, 900)
    res = test(mcl, urls)
    st = mcl.status()
    print "MultiRequestClient (QJT multi docs): %s (items: %d, size: %s)" % (res, st['cache_items'], st['cache_size'])

    mcl = MultiRequestFullCacheClient(10000, 900)
    res = test(mcl, urls)
    st = mcl.status()
    print "MultiRequestFullCacheClient (QJT multi docs, full cache): %s (items: %d, size: %s)" % (res, st['cache_items'], st['cache_size'])
