# -*- coding: utf-8 -*-

import time


class DummyBackend:
    """ Python Cache, lost when python stop """

    def __init__(self):
        self._caches = {}
        self._expires = {}

    def is_exists(self, key, **kwargs):
        stamp = self._expires.get(key, -1)
        if 0 <= stamp < time.time():
            del self._caches[key]
            del self._expires[key]
            return False
        else:
            return True
    
    def expire(self, key, **kwargs):
        stamp = int(kwargs.get('time', -1))
        if stamp < 0:
            self._expires[key] = -1
        else:
            self._expires[key] = time.time() + stamp

    def get_data(self, key, **kwargs):
        return self._caches.get(key)

    def set_data(self, key, value, **kwargs):
        self._caches[key] = value
        self.expire(key, **kwargs)
        return True
