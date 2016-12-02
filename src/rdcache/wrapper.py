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

    def __init__(self, converter, key, calculate, **kwargs):
        self.converter = converter
        self.key = key
        self.calculate = calculate
        self.default = kwargs.pop('default', self._ABSENT_DEFAULT)
        self.options = kwargs

    def _has_default(self):
        return self.default != self._ABSENT_DEFAULT

    def _get_cached(self, *args, **kwargs):
        if not self.converter.enabled:
            return self.calculate(*args, **kwargs)
        key = self.converter.prepare_key(self.key, *args, **kwargs)
        kwargs.update(self.options)
        return self.converter.get(key, **kwargs)

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
        if self.converter.enabled:
            key = self.converter.prepare_key(self.key, *args, **kwargs)
            kwargs.update(self.options)
            self.converter.set(key, value, **kwargs)
        return value

    def get(self, *args, **kwargs):
        try:
            return self._get_cached(*args, **kwargs)
        except KeyError:
            return self.refresh(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.get(*args, **kwargs)
