# -*- coding: utf-8 -*-

"""Caching utilities.
This library provides some classes to access different types of cache.

* Author: Gabriel Patiño <gabrielp@olx.com>
* Date:   2010-12-28

Copyright © 2010 OLX
"""

import time
import threading
import copy
import sys
import json
import hashlib

from lib import lru


def hashed_key(fn):
    def inner(*args, **kwargs):
        key = hashlib.md5(args[1]).hexdigest()
        args2 = []
        args2.append(args[0])
        args2.append(key)
        args2 = args2 + list(args[2:])
        args2 = tuple(args2)
        return fn(*args2)
    return fn
    return inner


class BaseCache(object):
    """Abstract class to be used as a base class for other Cache classes."""

    def get(self, key, default=None):
        """Try to access a key and return the stored value or default in case
        it's not there or has expired

        **Args:**

        * key: key to retrieve
        * default: (optional) The value to return if key is not found or
                   expired.

        **Returns:** Stored value or default
        """
        pass


    def set(self, key, value, ttl=60):
        """Stores value in key for ttl seconds.

        **Args:**

        * key: key to store
        * value: value to store
        * ttl: (optional) The amount of seconds to store the value. Defaults to
               60 seconds.
        """
        pass


    def delete(self, key):
        """Deletes the stored key failing silently in case it doesn't exist.

        **Args:**

        * key: key to delete
        """
        pass


    def clear(self):
        """Deletes all cached keys"""
        pass




class LocalCache(BaseCache):
    """LocalCache stores the cached data in memory. Use it wisely.
    Take into account that it can cache live python objects, and this objects
    won't be flushed by the garbage collector until they are removed from the
    LocalCache instance(s) that stores it.

    **Args:**

    * max_items *(int)*: (optional) Numer of max items that will be stored in
      the memory.
    """

    def __init__(self, max_items=1000):
        self._cache = {}
        self._lru = lru.LRU(max_items=max_items)
        self._lock = threading.RLock()
        super(LocalCache, self).__init__()

    @hashed_key
    def get(self, key, default=None):
        ttl = None
        with self._lock:
            if key in self._cache:
                value, ttl = self._cache[key]

        if ttl is not None:
            if ttl == 0 or ttl >= time.time():
                #res = self._lru.set(key)
                #if res:
                #    self.delete(res)
                return copy.deepcopy(value)
            else:
                self.delete(key)
        return default

    @hashed_key
    def set(self, key, value, ttl=60):
        data = copy.deepcopy(value)
        if ttl != 0:
            ttl = time.time() + ttl
        self._cache[key] = (data, ttl)
        #res = self._lru.set(key)
        #if res:
        #    self.delete(res)

    @hashed_key
    def delete(self, key):
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                #self._lru.delete(key)

    def clear(self):
        """ Deletes all cache keys. """
        with self._lock:
            self._cache = {}
            #self._lru.flush()

    def __len__(self):
        return len(self._cache)

    def __sizeof__(self):
        size = 0
        for v in self._cache.values():
            size += sys.getsizeof(str(v))
        return size


class InvalidCacheException(Exception):
    """Exception raised when trying to get an unexistant cache"""
    pass

