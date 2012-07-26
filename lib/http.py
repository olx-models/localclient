# -*- coding: utf-8 -*-

"""HTTP utilities

* Author: Gabriel Patiño <gabrielp@olx.com>
* Date:   2011-03-30

Copyright © 2011 OLX
"""

import urllib2
import mimetypes
from StringIO import StringIO
import zlib

class MultiMethodRequest(urllib2.Request):
    """Request class that extends urllib2.Request adding support for multiple
    request methods."""

    VALID_METHODS = ['GET', 'POST', 'DELETE', 'PUT', 'HEAD']

    def __init__(self, url, method=None, *args, **kwargs):
        if method is not None and method not in self.VALID_METHODS:
            method = None
        self.method = method
        urllib2.Request.__init__(self, url, *args, **kwargs)

    def get_method(self):
        if self.method is not None:
            return self.method
        return urllib2.Request.get_method(self)


def urlopen(url, data=None, method='GET', headers={}, timeout=10):
    """Extends urllib2.urlopen adding multi method support."""
    req = MultiMethodRequest(url, method=method, headers=headers)
    if isinstance(data, unicode):
        data = data.encode('utf-8')
    return urllib2.urlopen(req, data, timeout)


def ziped_post(url, data, headers={}, timeout=10, field_name='data'):
    ''' Send ziped request
        for use with php with file_get_contents('php://input');
        @param data must be string
    '''
    data = zlib.compress(data.encode('utf-8'))

    request = urllib2.Request(url, data=data)
    request.add_header('Cache-Control', 'no-cache')
    request.add_header('Content-Length', '%d' % len(data))
    request.add_header('Content-Type', 'application/zip')

    response = urllib2.urlopen(request).read().strip()
    return response
