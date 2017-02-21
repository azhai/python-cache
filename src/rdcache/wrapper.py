# -*- coding: utf-8 -*-


class CacheWrapper:
    """
    The result of using the cache decorator is an instance of
    CacheWrapper.

    Methods:

    get       (aliased as __call__) Get the value from the cache,
              recomputing and caching if necessary.

    cached    Get the cached value.  In case the value is not cached,
              you may pass a `default` keyword argument which will be
              used instead.  If no default is present, a `KeyError` will
              be thrown.

    refresh   Re-calculate and re-cache the value, regardless of the
              contents of the backend cache.
    """
    
    _ABSENT_DEFAULT = '###ABSENT_DEFAULT###'

    def __init__(self, handler, key, calculate, **kwargs):
        self.handler = handler
        self.key = key
        self.calculate = calculate
        self.default = kwargs.pop('default', self._ABSENT_DEFAULT)
        self.options = kwargs

    def _has_default(self):
        return self.default != self._ABSENT_DEFAULT

    def generate_key(self, *args, **kwargs):
        """ Generate cache key """
        if args:
            return self.key % args
        else:
            return self.key % kwargs

    def _get_cached(self, *args, **kwargs):
        if not self.handler.enabled:
            result = self.calculate(*args, **kwargs)
        else:
            key = self.generate_key(*args, **kwargs)
            kwargs.update(self.options)
            result = self.handler.load(key, **kwargs)
        if result is None and self._has_default():
            result = self.default
        return result

    def cached(self, *args, **kwargs):
        try:
            return self._get_cached(*args, **kwargs)
        except KeyError as err:
            if self._has_default():
                return self.default
            else:
                raise err

    def refresh(self, *args, **kwargs):
        value = self.calculate(*args, **kwargs)
        if self.handler.enabled:
            key = self.generate_key(*args, **kwargs)
            kwargs.update(self.options)
            self.handler.save(key, value, **kwargs)
        return value

    def get(self, *args, **kwargs):
        try:
            return self._get_cached(*args, **kwargs)
        except KeyError:
            return self.refresh(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.get(*args, **kwargs)
