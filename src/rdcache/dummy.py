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
    
    def is_exists(self, key, **kwargs):
        stamp = self._expire.get(key, -1)
        if 0 <= stamp < time.time():
            del self._cache[key]
            del self._expire[key]
            return False
        else:
            return True

    def get_data(self, key, **kwargs):
        return self._cache.get(key)

    def set_data(self, key, value, **kwargs):
        self._cache[key] = value
        self.expire(key, **kwargs)
        return True
