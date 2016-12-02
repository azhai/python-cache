# -*- coding: utf-8 -*-

import time


class DummyBackend:
    """ Python Cache, lost when python stop """
    def __init__(self):
        self._cache = {}
        self._expire = {}
    
    def expire(self, key, **kwargs):
        stamp = int(kwargs.get('time', -1))
        if stamp < 0:
            self._expire[key] = -1
        else:
            self._expire[key] = time.time() + stamp
    
    def is_expire(self, key):
        stamp = self._expire.get(key, -1)
        if 0 <= stamp < time.time():
            del self._cache[key]
            del self._expire[key]
            return True
        else:
            return False

    def set(self, key, value, **kwargs):
        self._cache[key] = value
        self.expire(key, **kwargs)

    def get(self, key, **kwargs):
        if not self.is_expire(key):
            return self._cache.get(key)
