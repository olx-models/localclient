# -*- coding: utf-8 -*-

"""LRU utilities.
This package provieds LRU functionality.

* Author: Martin Marrese <martinm@olx.com>
* Date:   2010-12-30

Copyright © 2010 OLX
"""

import threading


class LRU(object):
    """LRU tool.
   
    **Args:**

    * max_items *(int)*: Maximun number allowed
    """

    def __init__(self, max_items):
        self._list = []
        self._max_items = max_items
        self._lock = threading.RLock()

    def __len__(self):
        return len(self._list)

    def set(self, key):
        """Adds a new item in the list
        
        If the key is already present in the list, it resets it status and move
        it to the end of the list.
        If the limit is reached, the first element gets removed

        **Args:**
        
        * key *(string)*: Key to store in the db.

        **Returns:**
        None or the key removed
        """
        out = None
        with self._lock:
            if key in self._list:
                self.delete(key)
            self._list.append(key)
            if len(self._list) > self._max_items:
                out = self._list[0]
                self._list = self._list[1:]
        return out

    def delete(self, key):
        """Removes the key from the list

        **Args:**

        * key *(string)*: Key to remove
        """
        with self._lock:
            if key in self._list:
                self._list.remove(key)

    def flush(self):
        """Removes all entries from the list"""
        with self._lock:
            self._list = []
